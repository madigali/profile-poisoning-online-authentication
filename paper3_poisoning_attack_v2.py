#!/usr/bin/env python3
"""
paper3_poisoning_attack_v2.py

Paper 3 — held-out profile-poisoning experiment.

This script consumes the fixed ``paper3_cache`` created from the canonical
``hmog_revised_experiment.py`` pipeline.  It never trains or modifies the LSTM.

Protocol
--------
For every fold, victim, and repeat:

1. Build the initial score-profile from the victim's validation scores and
   calibrate the initial threshold with validation genuine/impostor scores.
2. Split test-set impostors by whole (source identity, session) groups into two
   disjoint pools before choosing an attack: a poisoning pool and a held-out
   probe pool.  Correlated windows from one source session cannot cross pools.
3. Construct one nested poisoning sequence of length max(K), where
   K = 0, 1, 2, 4, 8 by default.
4. Feed the same poisoning attempts to:
      * Frozen: fixed validation-calibrated threshold;
      * Blind EMA: every accepted attempt updates the profile;
      * Oracle EMA: attempts are scored but known impostors never update.
5. Freeze every profile after poisoning.  Evaluate future ASR on the disjoint
   impostor probe pool and FRR on genuine test samples without any updates.

Attack strategies
-----------------
``random``
    Uniform sampling without replacement from the poisoning pool.

``boundary``
    Initially accepted impostors, ranked by the positive margin above the
    initial decision threshold.  The closest accepted samples are used first.
    Thus the attack avoids the ceiling effect of selecting the highest scores.

The held-out probe set and eligible victim/repeat cohort are identical across
strategies and all K values.  Blind and Oracle also receive identical poisoning
sequences and probes.  K values are nested prefixes of the same sequence.

Because this attack-only phase contains no genuine adaptation observations,
Oracle EMA is deliberately a contamination control: it must remain numerically
equivalent to Frozen.  Its value is to verify that any Blind-Oracle difference
comes from accepted malicious profile updates rather than score selection.

Outputs
-------
``paper3_attack_v2_by_fold.csv``
    One macro-averaged row per fold/strategy/K.

``paper3_attack_v2_summary.csv``
    Across-fold mean, standard deviation, standard error, and 95% t interval
    for every reported numeric metric, grouped by strategy/K.

Rates in the CSV files are percentages.  Profile statistics remain in native
score units.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

import hmog_revised_experiment as core


DEFAULT_BUDGETS = (0, 1, 2, 4, 8)
DEFAULT_REPEATS = 100
DEFAULT_PROBE_FRACTION = 0.50
T95_DF4 = 2.7764451051977987


class InsufficientBoundaryCandidates(RuntimeError):
    """Raised when a victim has too few accepted near-boundary impostors."""


@dataclass(frozen=True)
class ProfileSnapshot:
    mean: float
    sigma: float
    threshold: float


def load_fold(cache_dir: Path, fold: int, drift: float = 0.0) -> dict[str, np.ndarray]:
    """Load scores and chronological metadata; do not load or train a model."""
    base_path = cache_dir / f"fold{fold}_base.npz"
    score_path = cache_dir / f"fold{fold}_D{drift:.1f}.npz"
    if not base_path.is_file():
        raise FileNotFoundError(f"Missing fixed cache file: {base_path}")
    if not score_path.is_file():
        raise FileNotFoundError(f"Missing fixed cache file: {score_path}")

    with np.load(base_path) as base, np.load(score_path) as scores:
        required_base = {"val_scores", "y_val"}
        required_scores = {
            "test_scores", "y_test", "session_test", "within_test"
        }
        missing_base = required_base.difference(base.files)
        missing_scores = required_scores.difference(scores.files)
        if missing_base or missing_scores:
            raise KeyError(
                "Cache schema mismatch. "
                f"Missing from {base_path.name}: {sorted(missing_base)}; "
                f"missing from {score_path.name}: {sorted(missing_scores)}"
            )
        return {
            "val_scores": np.asarray(base["val_scores"]),
            "y_val": np.asarray(base["y_val"]),
            "test_scores": np.asarray(scores["test_scores"]),
            "y_test": np.asarray(scores["y_test"]),
            "session_test": np.asarray(scores["session_test"]),
            "within_test": np.asarray(scores["within_test"]),
        }


def _finite_scalar_attr(obj: object, names: Iterable[str]) -> float | None:
    for name in names:
        if not hasattr(obj, name):
            continue
        value = getattr(obj, name)
        if callable(value):
            continue
        array = np.asarray(value)
        if array.size != 1:
            continue
        number = float(array.reshape(-1)[0])
        if np.isfinite(number):
            return number
    return None


def profile_snapshot(agent: object) -> ProfileSnapshot:
    """Read the canonical EMA state while tolerating common attribute names."""
    # The canonical Paper 2 implementation uses p/q.  The remaining aliases
    # make this script tolerant to harmless renaming without changing dynamics.
    mean = _finite_scalar_attr(agent, ("p", "mean", "mu", "m"))
    sigma = _finite_scalar_attr(agent, ("sigma", "std", "stdev"))

    if mean is None:
        raise AttributeError(
            "Could not find the EMA mean attribute. Expected one of "
            "mean/mu/m/p; available state is "
            f"{sorted(vars(agent)) if hasattr(agent, '__dict__') else type(agent)}"
        )

    if sigma is None:
        variance = _finite_scalar_attr(agent, ("variance", "var"))
        if variance is not None:
            sigma = math.sqrt(max(variance, 0.0))

    if sigma is None:
        # Canonical online EMA implementations commonly store E[x^2] as q/m2.
        second_moment = _finite_scalar_attr(
            agent, ("q", "second_moment", "mean_square", "m2")
        )
        if second_moment is not None:
            sigma = math.sqrt(max(second_moment - mean * mean, 0.0))

    if sigma is None:
        raise AttributeError(
            "Could not recover EMA sigma. Expected sigma/std, variance/var, "
            "or a second moment named q/second_moment/mean_square/m2; "
            f"available state is {sorted(vars(agent)) if hasattr(agent, '__dict__') else type(agent)}"
        )

    threshold = float(getattr(agent, "threshold"))
    return ProfileSnapshot(mean=mean, sigma=sigma, threshold=threshold)


def accepted_without_update(agent: object, score: float) -> bool:
    """Make a decision against the current profile without mutating it."""
    return bool(score >= float(getattr(agent, "threshold")))


def split_impostor_pool(
    impostor_pool: np.ndarray,
    y_test: np.ndarray,
    session_test: np.ndarray,
    rng: np.random.Generator,
    probe_fraction: float,
    min_poison_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Create source-identity/session-disjoint poison and probe pools."""
    impostor_pool = np.asarray(impostor_pool, dtype=np.int64)
    groups: dict[tuple[object, object], list[int]] = {}
    for index in impostor_pool:
        identity = np.asarray(y_test[index]).item()
        session = np.asarray(session_test[index]).item()
        groups.setdefault((identity, session), []).append(int(index))

    if len(groups) < 2:
        raise ValueError("Need at least two impostor identity/session groups")

    keys = list(groups)
    order = rng.permutation(len(keys))
    ordered = [np.asarray(groups[keys[i]], dtype=np.int64) for i in order]
    sizes = np.asarray([len(group) for group in ordered], dtype=int)
    cumulative = np.cumsum(sizes)
    target = len(impostor_pool) * probe_fraction
    feasible_cuts = [
        cut for cut in range(1, len(ordered))
        if len(impostor_pool) - cumulative[cut - 1] >= min_poison_size
    ]
    if not feasible_cuts:
        raise ValueError(
            f"Need at least {min_poison_size} poisoning candidates and one "
            f"held-out identity/session group, but only {len(impostor_pool)} "
            "impostor samples are available."
        )
    cut = min(feasible_cuts, key=lambda item: abs(cumulative[item - 1] - target))
    probe = np.concatenate(ordered[:cut])
    poisoning = np.concatenate(ordered[cut:])
    return poisoning, probe


def choose_poison_sequence(
    strategy: str,
    poisoning_pool: np.ndarray,
    victim_scores: np.ndarray,
    tau0: float,
    max_budget: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Choose one max-K sequence; smaller budgets use nested prefixes."""
    poisoning_pool = np.asarray(poisoning_pool, dtype=np.int64)
    if max_budget == 0:
        return np.empty(0, dtype=np.int64)
    if len(poisoning_pool) < max_budget:
        raise ValueError(
            f"Poisoning pool has {len(poisoning_pool)} samples, fewer than "
            f"max K={max_budget}."
        )

    if strategy == "random":
        return rng.choice(poisoning_pool, size=max_budget, replace=False)

    if strategy == "boundary":
        scores = victim_scores[poisoning_pool]
        accepted_mask = scores >= tau0
        accepted_idx = poisoning_pool[accepted_mask]
        accepted_scores = scores[accepted_mask]
        if len(accepted_idx) < max_budget:
            raise InsufficientBoundaryCandidates(
                f"Only {len(accepted_idx)} initially accepted poisoning "
                f"candidates are available for max K={max_budget}."
            )
        # Stable tie-breaking keeps the experiment deterministic.
        order = np.lexsort((accepted_idx, accepted_scores - tau0))
        return accepted_idx[order[:max_budget]]

    raise ValueError(f"Unknown attack strategy: {strategy}")


def _rate(values: Sequence[bool] | np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    return float(values.mean()) if values.size else float("nan")


def _profile_fields(prefix: str, before: ProfileSnapshot, after: ProfileSnapshot):
    return {
        f"{prefix}_mean_before": before.mean,
        f"{prefix}_mean_after": after.mean,
        f"{prefix}_mean_delta": after.mean - before.mean,
        f"{prefix}_sigma_before": before.sigma,
        f"{prefix}_sigma_after": after.sigma,
        f"{prefix}_sigma_delta": after.sigma - before.sigma,
        f"{prefix}_threshold_before": before.threshold,
        f"{prefix}_threshold_after": after.threshold,
        f"{prefix}_threshold_delta": after.threshold - before.threshold,
        f"{prefix}_threshold_drop": before.threshold - after.threshold,
    }


def evaluate_budget(
    sid: int,
    tau0: float,
    enrollment: np.ndarray,
    poison_idx: np.ndarray,
    probe_idx: np.ndarray,
    genuine_idx: np.ndarray,
    test_scores: np.ndarray,
) -> dict[str, float]:
    """Run poison phase, freeze state, then evaluate disjoint future probes."""
    blind = core.AdaptiveEMA.from_enrollment(enrollment, tau0)
    oracle = core.AdaptiveEMA.from_enrollment(enrollment, tau0)

    blind_before = profile_snapshot(blind)
    oracle_before = profile_snapshot(oracle)
    frozen_before = blind_before

    frozen_poison_accepts: list[bool] = []
    blind_poison_accepts: list[bool] = []
    oracle_poison_accepts: list[bool] = []

    for index in poison_idx:
        score = float(test_scores[index, sid])
        frozen_poison_accepts.append(score >= tau0)
        # Canonical label-blind behavior: acceptance triggers its normal update.
        blind_poison_accepts.append(bool(blind.decide(score)))
        # Oracle sees the same score but blocks the known-impostor update.
        oracle_poison_accepts.append(accepted_without_update(oracle, score))

    blind_after = profile_snapshot(blind)
    oracle_after = profile_snapshot(oracle)
    frozen_after = frozen_before

    probe_scores = np.asarray(test_scores[probe_idx, sid], dtype=float)
    genuine_scores = np.asarray(test_scores[genuine_idx, sid], dtype=float)

    thresholds = {
        "frozen": tau0,
        "ema_blind": blind_after.threshold,
        "ema_oracle": oracle_after.threshold,
    }
    result: dict[str, float] = {}
    poison_accepts = {
        "frozen": frozen_poison_accepts,
        "ema_blind": blind_poison_accepts,
        "ema_oracle": oracle_poison_accepts,
    }

    for method, threshold in thresholds.items():
        result[f"{method}_post_ASR"] = _rate(probe_scores >= threshold)
        result[f"{method}_post_FRR"] = _rate(genuine_scores < threshold)
        result[f"{method}_poison_accept_rate"] = (
            _rate(poison_accepts[method]) if len(poison_idx) else 0.0
        )

    # Only Blind EMA incorporates accepted malicious samples into its state.
    k = len(poison_idx)
    result["ema_blind_poison_updates"] = float(sum(blind_poison_accepts))
    result["ema_blind_MUR"] = _rate(blind_poison_accepts) if k else 0.0
    result["ema_oracle_poison_updates"] = 0.0
    result["ema_oracle_MUR"] = 0.0
    result["frozen_poison_updates"] = 0.0
    result["frozen_MUR"] = 0.0

    result.update(_profile_fields("frozen", frozen_before, frozen_after))
    result.update(_profile_fields("ema_blind", blind_before, blind_after))
    result.update(_profile_fields("ema_oracle", oracle_before, oracle_after))

    result["blind_minus_frozen_post_ASR"] = (
        result["ema_blind_post_ASR"] - result["frozen_post_ASR"]
    )
    result["blind_minus_oracle_post_ASR"] = (
        result["ema_blind_post_ASR"] - result["ema_oracle_post_ASR"]
    )
    result["blind_minus_oracle_post_FRR"] = (
        result["ema_blind_post_FRR"] - result["ema_oracle_post_FRR"]
    )
    # With malicious-only poisoning and blocked Oracle updates, these controls
    # must be identical.  A failure indicates accidental state mutation.
    if not (
        np.isclose(result["frozen_post_ASR"], result["ema_oracle_post_ASR"])
        and np.isclose(result["frozen_post_FRR"], result["ema_oracle_post_FRR"])
        and np.isclose(oracle_after.threshold, tau0)
    ):
        raise AssertionError("Oracle contamination control diverged from Frozen")
    return result


def parse_budgets(text: str) -> tuple[int, ...]:
    try:
        budgets = tuple(sorted({int(item.strip()) for item in text.split(",")}))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Budgets must be comma-separated integers") from exc
    if not budgets or budgets[0] < 0:
        raise argparse.ArgumentTypeError("Budgets must be non-negative")
    if 0 not in budgets:
        raise argparse.ArgumentTypeError("Budgets must include K=0 as the control")
    return budgets


def _seed(base: int, fold: int, sid: int, repeat: int, stream: int) -> int:
    # Separate deterministic random streams.  Strategy is deliberately absent
    # from the split seed so held-out probes match across attack strategies.
    return int(base + fold * 10_000_000 + sid * 100_000 + repeat * 10 + stream)


def _percentage_columns(columns: Iterable[str]) -> list[str]:
    markers = (
        "_ASR", "_FRR", "_MUR", "_accept_rate",
        "blind_minus_frozen_post_ASR",
        "blind_minus_oracle_post_ASR",
        "blind_minus_oracle_post_FRR",
    )
    return [name for name in columns if any(marker in name for marker in markers)]


def aggregate_by_fold(subject_rows: pd.DataFrame) -> pd.DataFrame:
    """Average repeats per subject, then macro-average subjects equally."""
    metric_cols = [
        col for col in subject_rows.select_dtypes(include=[np.number]).columns
        if col not in {"fold", "K", "sid", "repeat"}
    ]
    per_subject = (
        subject_rows.groupby(
            ["fold", "strategy", "K", "sid"], as_index=False
        )[metric_cols]
        .mean()
    )
    grouped = (
        per_subject.groupby(["fold", "strategy", "K"], as_index=False)[metric_cols]
        .mean()
        .sort_values(["fold", "strategy", "K"])
        .reset_index(drop=True)
    )
    counts = (
        subject_rows.groupby(["fold", "strategy", "K"], as_index=False)
        .agg(n_subject_repeat_rows=("sid", "size"), n_subjects=("sid", "nunique"))
    )
    return grouped.merge(counts, on=["fold", "strategy", "K"], how="left")


def make_summary(by_fold: pd.DataFrame) -> pd.DataFrame:
    excluded = {"fold", "K", "n_subject_repeat_rows", "n_subjects"}
    metric_cols = [
        col for col in by_fold.select_dtypes(include=[np.number]).columns
        if col not in excluded
    ]
    rows: list[dict[str, float | int | str]] = []
    for (strategy, budget), group in by_fold.groupby(["strategy", "K"], sort=True):
        for metric in metric_cols:
            values = group[metric].dropna().to_numpy(dtype=float)
            if values.size == 0:
                continue
            mean = float(values.mean())
            std = float(values.std(ddof=1)) if values.size > 1 else float("nan")
            sem = std / math.sqrt(values.size) if values.size > 1 else float("nan")
            # Five folds are expected; use the exact df=4 multiplier then.
            # The normal approximation is only a fallback for nonstandard runs.
            t95 = {2: 12.7062047364, 3: 4.3026527297, 4: 3.1824463053,
                   5: T95_DF4}
            critical = t95.get(values.size, 1.96)
            rows.append(
                {
                    "strategy": strategy,
                    "K": int(budget),
                    "metric": metric,
                    "n_folds": int(values.size),
                    "mean": mean,
                    "std_across_folds": std,
                    "sem": sem,
                    "ci95_low": mean - critical * sem,
                    "ci95_high": mean + critical * sem,
                }
            )
    return pd.DataFrame(rows)


def run(args: argparse.Namespace) -> None:
    cache_dir = Path(args.cache_dir)
    budgets: tuple[int, ...] = args.budgets
    max_budget = max(budgets)
    n_folds = int(getattr(core, "N_FOLDS", 5))
    rows: list[dict[str, float | int | str]] = []
    boundary_skips = 0

    for fold in range(1, n_folds + 1):
        data = load_fold(cache_dir, fold, drift=args.drift)
        val_scores = data["val_scores"]
        y_val = data["y_val"]
        test_scores = data["test_scores"]
        y_test = data["y_test"]
        session_test = data["session_test"]
        within_test = data["within_test"]

        if val_scores.ndim != 2 or test_scores.ndim != 2:
            raise ValueError("val_scores and test_scores must be 2-D matrices")
        if val_scores.shape[1] != test_scores.shape[1]:
            raise ValueError("Validation and test score matrices disagree on users")

        print(f"\nFold {fold}/{n_folds}")
        fold_start = len(rows)

        for sid in range(test_scores.shape[1]):
            enrollment = np.asarray(val_scores[y_val == sid, sid], dtype=float)
            validation_impostor = np.asarray(val_scores[y_val != sid, sid], dtype=float)
            genuine_idx = core.chronology_order(
                session_test,
                within_test,
                np.flatnonzero(y_test == sid),
            )
            impostor_pool = np.flatnonzero(y_test != sid)

            if len(enrollment) < 2 or len(validation_impostor) < 1:
                continue
            if len(genuine_idx) < 1 or len(impostor_pool) <= max_budget:
                continue

            _, tau0 = core.eer_from_scores(enrollment, validation_impostor)

            for repeat in range(args.repeats):
                split_rng = np.random.default_rng(
                    _seed(args.seed, fold, sid, repeat, stream=0)
                )
                poisoning_pool, probe_idx = split_impostor_pool(
                    impostor_pool=impostor_pool,
                    y_test=y_test,
                    session_test=session_test,
                    rng=split_rng,
                    probe_fraction=args.probe_fraction,
                    min_poison_size=max(max_budget, 1),
                )

                # Establish a common paired cohort first.  If boundary is not
                # feasible, skip both strategies for this victim/repeat rather
                # than biasing boundary toward unusually vulnerable cases.
                sequences: dict[str, np.ndarray] = {}
                cohort_is_eligible = True
                for strategy_index, strategy in enumerate(("random", "boundary"), 1):
                    attack_rng = np.random.default_rng(
                        _seed(args.seed, fold, sid, repeat, stream=strategy_index)
                    )
                    try:
                        full_sequence = choose_poison_sequence(
                            strategy=strategy,
                            poisoning_pool=poisoning_pool,
                            victim_scores=test_scores[:, sid],
                            tau0=float(tau0),
                            max_budget=max_budget,
                            rng=attack_rng,
                        )
                    except InsufficientBoundaryCandidates:
                        boundary_skips += 1
                        cohort_is_eligible = False
                        break
                    sequences[strategy] = full_sequence

                if not cohort_is_eligible:
                    continue

                for strategy, full_sequence in sequences.items():
                    for budget in budgets:
                        poison_idx = full_sequence[:budget]
                        metrics = evaluate_budget(
                            sid=sid,
                            tau0=float(tau0),
                            enrollment=enrollment,
                            poison_idx=poison_idx,
                            probe_idx=probe_idx,
                            genuine_idx=genuine_idx,
                            test_scores=test_scores,
                        )
                        rows.append(
                            {
                                "fold": fold,
                                "strategy": strategy,
                                "K": budget,
                                "sid": sid,
                                "repeat": repeat,
                                "n_enrollment": len(enrollment),
                                "n_genuine_probes": len(genuine_idx),
                                "n_impostor_probes": len(probe_idx),
                                "n_poisoning_pool": len(poisoning_pool),
                                "tau0": float(tau0),
                                **metrics,
                            }
                        )

        fold_rows = pd.DataFrame(rows[fold_start:])
        if fold_rows.empty:
            print("  no eligible subject/repeat rows")
            continue
        preview = aggregate_by_fold(fold_rows)
        for _, item in preview.iterrows():
            print(
                f"  {item['strategy']:8s} K={int(item['K']):>2d} | "
                f"Frozen={100*item['frozen_post_ASR']:.2f}% | "
                f"Blind={100*item['ema_blind_post_ASR']:.2f}% | "
                f"Oracle={100*item['ema_oracle_post_ASR']:.2f}% | "
                f"Blind-Oracle={100*item['blind_minus_oracle_post_ASR']:+.2f} pp | "
                f"MUR={100*item['ema_blind_MUR']:.2f}%"
            )

    subject_rows = pd.DataFrame(rows)
    if subject_rows.empty:
        raise RuntimeError(
            "No experiment rows were produced. Check the cache schema and "
            "whether boundary candidates exist above the initial threshold."
        )

    by_fold = aggregate_by_fold(subject_rows)
    percentage_cols = _percentage_columns(by_fold.columns)
    by_fold_export = by_fold.copy()
    by_fold_export[percentage_cols] = 100.0 * by_fold_export[percentage_cols]

    output_by_fold = Path(args.output_by_fold)
    output_summary = Path(args.output_summary)
    output_by_fold.parent.mkdir(parents=True, exist_ok=True)
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    by_fold_export.to_csv(output_by_fold, index=False)

    summary = make_summary(by_fold_export)
    summary.to_csv(output_summary, index=False)

    print("\n" + "=" * 96)
    print(f"HELD-OUT POISONING SUMMARY ACROSS {n_folds} FOLDS")
    print("=" * 96)
    key_metrics = {
        "frozen_post_ASR",
        "ema_blind_post_ASR",
        "ema_oracle_post_ASR",
        "blind_minus_oracle_post_ASR",
        "ema_blind_MUR",
        "ema_blind_threshold_delta",
    }
    compact = summary[summary["metric"].isin(key_metrics)].pivot_table(
        index=["strategy", "K"], columns="metric", values="mean"
    )
    print(compact.round(4).to_string())
    print(f"\nSaved fold results: {output_by_fold.resolve()}")
    print(f"Saved summary:      {output_summary.resolve()}")
    if boundary_skips:
        print(
            f"Warning: skipped {boundary_skips} victim/repeat boundary runs "
            f"with fewer than {max_budget} initially accepted candidates."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Held-out profile-poisoning evaluation using fixed Paper 3 scores."
    )
    parser.add_argument("--cache-dir", default="paper3_cache")
    parser.add_argument("--drift", type=float, default=0.0)
    parser.add_argument(
        "--budgets",
        type=parse_budgets,
        default=DEFAULT_BUDGETS,
        help="Comma-separated attack budgets; must include 0 (default: 0,1,2,4,8).",
    )
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument(
        "--probe-fraction",
        type=float,
        default=DEFAULT_PROBE_FRACTION,
        help="Fraction of test impostors reserved before attack selection (default: 0.5).",
    )
    parser.add_argument(
        "--output-by-fold", default="paper3_attack_v2_by_fold.csv"
    )
    parser.add_argument(
        "--output-summary", default="paper3_attack_v2_summary.csv"
    )
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least 1")
    if not 0.0 < args.probe_fraction < 1.0:
        parser.error("--probe-fraction must be strictly between 0 and 1")
    return args


if __name__ == "__main__":
    run(parse_args())
