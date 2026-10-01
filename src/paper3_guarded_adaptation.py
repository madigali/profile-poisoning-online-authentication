#!/usr/bin/env python3
"""Confidence-gated EMA evaluation on the fixed Paper 3 attack-v2 protocol.

The script reuses the canonical ``paper3_poisoning_attack_v2.py`` functions for
cache loading, poison/probe splitting, boundary selection, seeds, and profile
inspection.  No LSTM is trained or loaded.

Compared policies
-----------------
* Frozen: no online updates.
* Blind EMA: every authenticated observation updates the EMA.
* Oracle EMA: malicious observations never update; genuine observations may.
* Guarded EMA: authentication and update authorization are separated by

      T_update = T_auth + lambda * (mu_enroll - T_auth)

  where ``mu_enroll`` is fixed and ``T_auth`` follows the current EMA profile.

Post-poison ASR/FRR/HTER and profile deltas are measured before any genuine
adaptation.  GUR is measured by replaying the chronological genuine stream on a
copy of the post-poison state, so it cannot change the security endpoint.

Rates are stored as percentages in CSV outputs; profile values stay in native
score units.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import math
import platform
import shlex
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


DEFAULT_BUDGETS = (0, 1, 2, 4, 8)
DEFAULT_LAMBDAS = (0.00, 0.25, 0.50, 0.75, 1.00)
DEFAULT_REPEATS = 100
DEFAULT_PROBE_FRACTION = 0.50
T95 = {2: 12.7062047364, 3: 4.3026527297, 4: 3.1824463053,
       5: 2.7764451052}
RATE_COLUMNS = {
    "post_ASR", "post_FRR", "HTER", "MUR", "GUR",
    "poison_accept_rate", "genuine_auth_rate",
}


@dataclass(frozen=True)
class Policy:
    policy_id: str
    method: str
    lambda_value: float

    @property
    def lambda_label(self) -> str:
        return "" if self.lambda_value < 0 else f"{self.lambda_value:.2f}"


def policies(lambdas: Sequence[float]) -> list[Policy]:
    base = [
        Policy("frozen", "Frozen", -1.0),
        Policy("blind", "Blind EMA", -1.0),
        Policy("oracle", "Oracle EMA", -1.0),
    ]
    return base + [
        Policy(f"guarded_{value:.2f}", "Guarded EMA", float(value))
        for value in lambdas
    ]


def load_canonical_modules(source_dir: Path):
    """Import the exact core and attack-v2 implementation from the source dir."""
    source_dir = source_dir.resolve()
    code_dir = source_dir / "src"
    if not code_dir.is_dir():
        code_dir = source_dir
    required = [
        code_dir / "hmog_revised_experiment.py",
        code_dir / "paper3_poisoning_attack_v2.py",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing canonical source file(s): " + ", ".join(missing))
    sys.path.insert(0, str(code_dir))
    try:
        core = importlib.import_module("hmog_revised_experiment")
        attack_v2 = importlib.import_module("paper3_poisoning_attack_v2")
    finally:
        sys.path.pop(0)
    return core, attack_v2


def parse_number_list(text: str, *, integer: bool) -> tuple:
    convert = int if integer else float
    try:
        values = tuple(sorted({convert(item.strip()) for item in text.split(",")}))
    except ValueError as exc:
        kind = "integers" if integer else "numbers"
        raise argparse.ArgumentTypeError(f"Expected comma-separated {kind}") from exc
    if not values:
        raise argparse.ArgumentTypeError("List cannot be empty")
    return values


def parse_budgets(text: str) -> tuple[int, ...]:
    values = parse_number_list(text, integer=True)
    if values[0] < 0 or 0 not in values:
        raise argparse.ArgumentTypeError("Budgets must be non-negative and include 0")
    return values


def parse_lambdas(text: str) -> tuple[float, ...]:
    values = parse_number_list(text, integer=False)
    if any(value < 0.0 or value > 1.0 for value in values):
        raise argparse.ArgumentTypeError("Lambda values must be in [0, 1]")
    if 0.0 not in values:
        raise argparse.ArgumentTypeError("Lambda grid must include 0.00 sanity control")
    return values


def update_threshold(agent: object, mu_enroll: float, lambda_value: float) -> float:
    auth_threshold = float(getattr(agent, "threshold"))
    return auth_threshold + lambda_value * (mu_enroll - auth_threshold)


def should_update(policy: Policy, agent: object, score: float, mu_enroll: float,
                  *, genuine: bool) -> bool:
    """Decide update authorization without mutating the agent."""
    authenticated = score >= float(getattr(agent, "threshold"))
    if not authenticated or policy.method == "Frozen":
        return False
    if policy.method == "Oracle EMA":
        return genuine
    if policy.method == "Blind EMA":
        return True
    return score >= update_threshold(agent, mu_enroll, policy.lambda_value)


def process_stream(policy: Policy, agent: object, scores: Iterable[float],
                   mu_enroll: float, *, genuine: bool) -> tuple[int, int]:
    """Return authentication and update counts while applying authorized EMA updates."""
    accepted = updates = 0
    for raw_score in scores:
        score = float(raw_score)
        authenticated = score >= float(getattr(agent, "threshold"))
        accepted += int(authenticated)
        if should_update(policy, agent, score, mu_enroll, genuine=genuine):
            # Canonical decide() performs the exact Paper 2 EMA update.
            if not bool(agent.decide(score)):
                raise AssertionError("Authorized update was rejected by canonical EMA")
            updates += 1
    return accepted, updates


def rate(count: int, denominator: int) -> float:
    return float(count / denominator) if denominator else 0.0


def profile_fields(before, after) -> dict[str, float]:
    return {
        "mean_before": before.mean,
        "mean_after": after.mean,
        "mean_delta": after.mean - before.mean,
        "sigma_before": before.sigma,
        "sigma_after": after.sigma,
        "sigma_delta": after.sigma - before.sigma,
        "threshold_before": before.threshold,
        "threshold_after": after.threshold,
        "threshold_delta": after.threshold - before.threshold,
    }


def evaluate_policy(policy: Policy, sid: int, tau0: float, enrollment: np.ndarray,
                    poison_idx: np.ndarray, probe_idx: np.ndarray,
                    genuine_idx: np.ndarray, test_scores: np.ndarray,
                    core, attack_v2) -> dict[str, float | int | str]:
    agent = core.AdaptiveEMA.from_enrollment(enrollment, tau0)
    before = attack_v2.profile_snapshot(agent)
    mu_enroll = float(np.mean(enrollment))

    poison_scores = np.asarray(test_scores[poison_idx, sid], dtype=float)
    poison_accepts, malicious_updates = process_stream(
        policy, agent, poison_scores, mu_enroll, genuine=False
    )
    after = attack_v2.profile_snapshot(agent)

    probe_scores = np.asarray(test_scores[probe_idx, sid], dtype=float)
    genuine_scores = np.asarray(test_scores[genuine_idx, sid], dtype=float)
    post_asr = float(np.mean(probe_scores >= after.threshold))
    post_frr = float(np.mean(genuine_scores < after.threshold))

    # Clean counterfactual replay: it measures genuine update availability but
    # cannot alter the already measured post-poison security/performance state.
    clean_agent = copy.deepcopy(agent)
    genuine_accepts, genuine_updates = process_stream(
        policy, clean_agent, genuine_scores, mu_enroll, genuine=True
    )

    result: dict[str, float | int | str] = {
        "policy_id": policy.policy_id,
        "method": policy.method,
        "lambda": policy.lambda_label,
        "lambda_value": policy.lambda_value,
        "post_ASR": post_asr,
        "post_FRR": post_frr,
        "HTER": 0.5 * (post_asr + post_frr),
        "poison_accept_rate": rate(poison_accepts, len(poison_scores)),
        "malicious_updates": malicious_updates,
        "MUR": rate(malicious_updates, len(poison_scores)),
        "genuine_auth_rate": rate(genuine_accepts, len(genuine_scores)),
        "genuine_updates": genuine_updates,
        "GUR": rate(genuine_updates, len(genuine_scores)),
        "mu_enroll": mu_enroll,
        "update_threshold_initial": (
            float("nan") if policy.lambda_value < 0
            else tau0 + policy.lambda_value * (mu_enroll - tau0)
        ),
        **profile_fields(before, after),
    }
    return result


def assert_lambda_zero_matches_blind(rows: list[dict], *, atol: float = 1e-12) -> None:
    blind = next(row for row in rows if row["policy_id"] == "blind")
    guarded = next(row for row in rows if row["policy_id"] == "guarded_0.00")
    fields = [
        "post_ASR", "post_FRR", "HTER", "poison_accept_rate",
        "malicious_updates", "MUR", "genuine_updates", "GUR",
        "mean_after", "sigma_after", "threshold_after",
        "mean_delta", "sigma_delta", "threshold_delta",
    ]
    failures = [
        name for name in fields
        if not np.isclose(float(blind[name]), float(guarded[name]), atol=atol, rtol=0.0)
    ]
    if failures:
        raise AssertionError(
            "Guarded lambda=0 failed Blind EMA sanity check: " + ", ".join(failures)
        )


def percentage_export(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    columns = [name for name in RATE_COLUMNS if name in out.columns]
    out[columns] = 100.0 * out[columns]
    return out


def aggregate_by_fold(subject_rows: pd.DataFrame) -> pd.DataFrame:
    keys = ["fold", "strategy", "K", "policy_id", "method", "lambda", "lambda_value"]
    excluded = set(keys + ["sid", "repeat"])
    metrics = [
        name for name in subject_rows.select_dtypes(include=[np.number]).columns
        if name not in excluded
    ]
    subject = (
        subject_rows.groupby(
            ["fold", "strategy", "K", "policy_id", "method", "lambda", "lambda_value", "sid"],
            as_index=False, dropna=False,
        )[metrics].mean()
    )
    folded = (
        subject.groupby(keys, as_index=False, dropna=False)[metrics].mean()
        .sort_values(["fold", "strategy", "K", "lambda_value", "policy_id"])
    )
    counts = (
        subject_rows.groupby(keys, as_index=False, dropna=False)
        .agg(n_subject_repeat_rows=("sid", "size"), n_subjects=("sid", "nunique"))
    )
    return folded.merge(counts, on=keys, how="left")


def make_summary(by_fold: pd.DataFrame) -> pd.DataFrame:
    keys = ["strategy", "K", "policy_id", "method", "lambda", "lambda_value"]
    excluded = set(keys + ["fold", "n_subject_repeat_rows", "n_subjects"])
    metrics = [
        name for name in by_fold.select_dtypes(include=[np.number]).columns
        if name not in excluded
    ]
    rows: list[dict] = []
    for key, group in by_fold.groupby(keys, sort=True, dropna=False):
        identity = dict(zip(keys, key))
        for metric in metrics:
            values = group[metric].dropna().to_numpy(dtype=float)
            if not len(values):
                continue
            mean = float(values.mean())
            std = float(values.std(ddof=1)) if len(values) > 1 else float("nan")
            sem = std / math.sqrt(len(values)) if len(values) > 1 else float("nan")
            critical = T95.get(len(values), 1.96)
            rows.append({
                **identity, "metric": metric, "n_folds": len(values),
                "mean": mean, "std_across_folds": std, "sem": sem,
                "ci95_low": mean - critical * sem,
                "ci95_high": mean + critical * sem,
            })
    return pd.DataFrame(rows)


def make_tradeoff(summary: pd.DataFrame) -> pd.DataFrame:
    wanted = [
        "post_ASR", "post_FRR", "HTER", "MUR", "GUR",
        "mean_delta", "sigma_delta", "threshold_delta",
    ]
    table = (
        summary[summary["metric"].isin(wanted)]
        .pivot(index=["strategy", "K", "policy_id", "method", "lambda", "lambda_value"],
               columns="metric", values="mean")
        .reset_index()
    )
    order = {"frozen": 0, "blind": 1, "oracle": 2}
    table["policy_order"] = table["policy_id"].map(order).fillna(
        3.0 + table["lambda_value"].clip(lower=0.0)
    )
    return table.sort_values(["strategy", "K", "policy_order"]).drop(columns="policy_order")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_output_dir(text: str | None) -> Path:
    if text:
        path = Path(text)
        if path.exists() and any(path.iterdir()):
            raise FileExistsError(f"Refusing to overwrite non-empty output directory: {path}")
        return path
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path("results") / f"{stamp}-guarded-ema"


def run(args: argparse.Namespace) -> Path:
    source_dir = Path(args.source_dir).resolve()
    cache_dir = Path(args.cache_dir).resolve() if args.cache_dir else source_dir / "paper3_cache"
    output_dir = resolve_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    core, attack_v2 = load_canonical_modules(source_dir)
    policy_grid = policies(args.lambdas)
    max_budget = max(args.budgets)
    n_folds = int(getattr(core, "N_FOLDS", 5))
    all_rows: list[dict] = []
    exclusions: list[dict] = []

    config = {
        "source_dir": str(source_dir), "cache_dir": str(cache_dir),
        "drift": args.drift, "budgets": list(args.budgets),
        "lambdas": list(args.lambdas), "repeats": args.repeats,
        "seed": args.seed, "probe_fraction": args.probe_fraction,
        "n_folds": n_folds,
        "gur_definition": "chronological genuine clean replay on copied post-poison state",
    }
    (output_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    status = "running"
    try:
        for fold in range(1, n_folds + 1):
            data = attack_v2.load_fold(cache_dir, fold, drift=args.drift)
            val_scores, y_val = data["val_scores"], data["y_val"]
            test_scores, y_test = data["test_scores"], data["y_test"]
            session_test, within_test = data["session_test"], data["within_test"]
            fold_start = len(all_rows)

            for sid in range(test_scores.shape[1]):
                enrollment = np.asarray(val_scores[y_val == sid, sid], dtype=float)
                val_impostor = np.asarray(val_scores[y_val != sid, sid], dtype=float)
                genuine_idx = core.chronology_order(
                    session_test, within_test, np.flatnonzero(y_test == sid)
                )
                impostor_idx = np.flatnonzero(y_test != sid)
                if len(enrollment) < 2 or not len(val_impostor) or not len(genuine_idx):
                    exclusions.append({"fold": fold, "sid": sid, "repeat": "",
                                       "reason": "insufficient enrollment/validation/genuine data"})
                    continue
                _, tau0 = core.eer_from_scores(enrollment, val_impostor)

                for repeat in range(args.repeats):
                    split_rng = np.random.default_rng(
                        attack_v2._seed(args.seed, fold, sid, repeat, stream=0)
                    )
                    try:
                        poisoning_pool, probe_idx = attack_v2.split_impostor_pool(
                            impostor_pool=impostor_idx, y_test=y_test,
                            session_test=session_test, rng=split_rng,
                            probe_fraction=args.probe_fraction,
                            min_poison_size=max(max_budget, 1),
                        )
                    except ValueError as exc:
                        exclusions.append({"fold": fold, "sid": sid, "repeat": repeat,
                                           "reason": str(exc)})
                        continue

                    sequences = {}
                    eligible = True
                    for stream, strategy in enumerate(("random", "boundary"), 1):
                        attack_rng = np.random.default_rng(
                            attack_v2._seed(args.seed, fold, sid, repeat, stream=stream)
                        )
                        try:
                            sequences[strategy] = attack_v2.choose_poison_sequence(
                                strategy, poisoning_pool, test_scores[:, sid],
                                float(tau0), max_budget, attack_rng,
                            )
                        except attack_v2.InsufficientBoundaryCandidates as exc:
                            exclusions.append({"fold": fold, "sid": sid, "repeat": repeat,
                                               "reason": str(exc)})
                            eligible = False
                            break
                    if not eligible:
                        continue

                    for strategy, sequence in sequences.items():
                        for budget in args.budgets:
                            condition_rows = []
                            for policy in policy_grid:
                                metrics = evaluate_policy(
                                    policy, sid, float(tau0), enrollment,
                                    sequence[:budget], probe_idx, genuine_idx,
                                    test_scores, core, attack_v2,
                                )
                                condition_rows.append(metrics)
                                all_rows.append({
                                    "fold": fold, "strategy": strategy, "K": budget,
                                    "sid": sid, "repeat": repeat,
                                    "n_enrollment": len(enrollment),
                                    "n_genuine_probes": len(genuine_idx),
                                    "n_impostor_probes": len(probe_idx),
                                    "n_poisoning_pool": len(poisoning_pool),
                                    "tau0": float(tau0), **metrics,
                                })
                            assert_lambda_zero_matches_blind(condition_rows)

            fold_frame = pd.DataFrame(all_rows[fold_start:])
            if fold_frame.empty:
                print(f"Fold {fold}/{n_folds}: no eligible rows", flush=True)
            else:
                preview = percentage_export(aggregate_by_fold(fold_frame))
                key = preview[(preview["strategy"] == "boundary") &
                              (preview["K"] == max_budget)]
                compact = ", ".join(
                    f"{row.policy_id}: ASR={row.post_ASR:.2f}% MUR={row.MUR:.2f}% GUR={row.GUR:.2f}%"
                    for row in key.itertuples()
                )
                print(f"Fold {fold}/{n_folds}: {compact}", flush=True)

        subject_rows = pd.DataFrame(all_rows)
        if subject_rows.empty:
            raise RuntimeError("No eligible experiment rows were produced")
        by_fold = percentage_export(aggregate_by_fold(subject_rows))
        summary = make_summary(by_fold)
        tradeoff = make_tradeoff(summary)

        percentage_export(subject_rows).to_csv(output_dir / "subject_repeat_metrics.csv", index=False)
        by_fold.to_csv(output_dir / "paper3_guarded_by_fold.csv", index=False)
        summary.to_csv(output_dir / "paper3_guarded_summary.csv", index=False)
        tradeoff.to_csv(output_dir / "paper3_guarded_tradeoff.csv", index=False)
        pd.DataFrame(exclusions, columns=["fold", "sid", "repeat", "reason"]).to_csv(
            output_dir / "exclusions.csv", index=False
        )
        status = "complete"
        print("\nBoundary, maximum K trade-off (across-fold means):")
        print(tradeoff[(tradeoff["strategy"] == "boundary") &
                       (tradeoff["K"] == max_budget)].drop(
                           columns=["policy_id", "lambda_value"]
                       ).round(5).to_string(index=False))
        return output_dir
    finally:
        cache_hashes = {
            path.name: sha256(path)
            for path in sorted(cache_dir.glob("fold*_base.npz"))
        }
        cache_hashes.update({
            path.name: sha256(path)
            for path in sorted(cache_dir.glob(f"fold*_D{args.drift:.1f}.npz"))
        })
        manifest = {
            "status": status,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "command": shlex.join(sys.argv),
            "python": sys.version,
            "platform": platform.platform(),
            "source_hashes": {
                "hmog_revised_experiment.py": sha256(Path(core.__file__).resolve()),
                "paper3_poisoning_attack_v2.py": sha256(Path(attack_v2.__file__).resolve()),
                "paper3_guarded_adaptation.py": sha256(Path(__file__).resolve()),
            },
            "cache_hashes": cache_hashes,
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir", default=".",
        help="Project root containing src/ and the fixed score cache",
    )
    parser.add_argument("--cache-dir", default=None,
                        help="Fixed score cache (default: SOURCE_DIR/paper3_cache)")
    parser.add_argument("--drift", type=float, default=0.0)
    parser.add_argument("--budgets", type=parse_budgets, default=DEFAULT_BUDGETS)
    parser.add_argument("--lambdas", type=parse_lambdas, default=DEFAULT_LAMBDAS)
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--probe-fraction", type=float, default=DEFAULT_PROBE_FRACTION)
    parser.add_argument("--output-dir", default=None,
                        help="New output directory (default: timestamped results directory)")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    if not 0.0 < args.probe_fraction < 1.0:
        parser.error("--probe-fraction must be strictly between 0 and 1")
    return args


if __name__ == "__main__":
    destination = run(parse_args())
    print(f"\nSaved guarded-adaptation run: {destination.resolve()}")
