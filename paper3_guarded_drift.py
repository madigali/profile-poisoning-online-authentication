#!/usr/bin/env python3
"""Clean-drift utility experiment for Frozen, Blind, Oracle and Guarded EMA.

The script uses fixed Paper 3 score caches and never trains the LSTM.  Genuine
test observations are paired within session: ``within=0`` is adaptation-only
and the later ``within=10`` sequence is a probe-only checkpoint.

Scenarios
---------
global
    Genuine and impostor scores both come from the selected D cache.  This uses
    the Paper 2 global synthetic drift transformation.
claimant_only
    Genuine scores come from the selected D cache, while impostor scores always
    come from D=0.  This isolates owner drift from impostor-distribution drift.

Statistical unit
----------------
There are no Monte Carlo repeats.  Fold summaries are descriptive.  For paired
uncertainty, subject metrics are first averaged across folds, then subjects are
resampled with replacement in a paired bootstrap.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import paper3_guarded_adaptation as guard


DEFAULT_DRIFTS = (0.0, 1.0, 2.0)
DEFAULT_LAMBDAS = (0.25,)
DEFAULT_BOOTSTRAPS = 10_000
RATE_COLUMNS = {
    "early_FRR", "late_FRR", "overall_FRR", "early_FAR", "late_FAR",
    "overall_FAR", "final_all_FAR", "FAR", "HTER", "GUR",
    "adaptation_auth_rate", "adaptation_gain", "hter_gain", "recovery_DiD",
    "checkpoint_FAR",
    "frozen_late_FRR", "frozen_HTER", "frozen_early_FRR",
}


def parse_floats(text: str, *, bounded: bool = False) -> tuple[float, ...]:
    try:
        values = tuple(sorted({float(item.strip()) for item in text.split(",")}))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected comma-separated numbers") from exc
    if not values:
        raise argparse.ArgumentTypeError("List cannot be empty")
    if bounded and any(value < 0.0 or value > 1.0 for value in values):
        raise argparse.ArgumentTypeError("Values must be in [0, 1]")
    return values


def parse_drifts(text: str) -> tuple[float, ...]:
    values = parse_floats(text)
    if 0.0 not in values:
        raise argparse.ArgumentTypeError("Drift levels must include D=0 sanity control")
    if any(value < 0.0 for value in values):
        raise argparse.ArgumentTypeError("Drift levels must be non-negative")
    return values


def parse_lambdas(text: str) -> tuple[float, ...]:
    return parse_floats(text, bounded=True)


def session_pairs(indices: np.ndarray, session: np.ndarray, within: np.ndarray) -> list[tuple[int, int, int]]:
    """Return chronological (session, adaptation, checkpoint) pairs."""
    pairs: list[tuple[int, int, int]] = []
    indices = np.asarray(indices, dtype=np.int64)
    for session_id in sorted(map(int, np.unique(session[indices]))):
        here = indices[session[indices] == session_id]
        by_within = {int(within[index]): int(index) for index in here}
        if 0 in by_within and 10 in by_within:
            pairs.append((session_id, by_within[0], by_within[10]))
    if len(pairs) < 4:
        raise ValueError("Need at least four complete within=0/within=10 session pairs")
    adaptation = {adapt for _, adapt, _ in pairs}
    probes = {probe for _, _, probe in pairs}
    if adaptation & probes:
        raise AssertionError("Adaptation and checkpoint probes overlap")
    return pairs


def split_early_late(values: Sequence) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(values)
    if len(values) < 4:
        raise ValueError("Need at least four session checkpoints")
    return values[:2], values[-2:]


def _fraction(values: Sequence[bool] | np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    return float(values.mean()) if len(values) else float("nan")


def force_ema_update(agent: object, score: float) -> None:
    """Apply the canonical EMA moment update without authentication gating."""
    required = ("mean", "second_moment", "alpha")
    missing = [name for name in required if not hasattr(agent, name)]
    if missing:
        raise AttributeError(f"Oracle-all requires canonical EMA fields: {missing}")
    alpha = float(agent.alpha)
    agent.mean = (1.0 - alpha) * float(agent.mean) + alpha * float(score)
    agent.second_moment = (
        (1.0 - alpha) * float(agent.second_moment) + alpha * float(score) ** 2
    )


def evaluate_subject_policy(
    policy: guard.Policy,
    sid: int,
    tau0: float,
    enrollment: np.ndarray,
    chronological_genuine: np.ndarray,
    genuine_scores: np.ndarray,
    impostor_score_matrix: np.ndarray,
    y_test: np.ndarray,
    session_test: np.ndarray,
    within_test: np.ndarray,
    core,
    attack_v2,
) -> tuple[dict, list[dict]]:
    """Run one deterministic genuine stream and return metrics/checkpoints."""
    pairs = session_pairs(chronological_genuine, session_test, within_test)
    agent = core.AdaptiveEMA.from_enrollment(enrollment, tau0)
    before = attack_v2.profile_snapshot(agent)
    mu_enroll = float(np.mean(enrollment))
    if not mu_enroll > tau0:
        raise AssertionError("Initial enrollment mean must exceed authentication threshold")
    adaptation_attempts = adaptation_accepts = updates = 0
    non_stricter_gate_states = 0
    checkpoint_rows: list[dict] = []
    probe_rejections: list[bool] = []
    checkpoint_fars: list[float] = []

    for checkpoint, (session_id, adaptation_index, probe_index) in enumerate(pairs):
        adaptation_score = float(genuine_scores[adaptation_index, sid])
        adaptation_attempts += 1
        auth_threshold = float(agent.threshold)
        authenticated = adaptation_score >= auth_threshold
        adaptation_accepts += int(authenticated)
        update_gate = float("nan")
        if policy.method == "Guarded EMA" and policy.lambda_value > 0:
            update_gate = guard.update_threshold(agent, mu_enroll, policy.lambda_value)
            if update_gate <= auth_threshold:
                non_stricter_gate_states += 1
        updated = False
        if policy.method == "Oracle-all-genuine":
            force_ema_update(agent, adaptation_score)
            updates += 1
            updated = True
        elif guard.should_update(policy, agent, adaptation_score, mu_enroll, genuine=True):
            if not bool(agent.decide(adaptation_score)):
                raise AssertionError("Canonical EMA rejected an authorized genuine update")
            updates += 1
            updated = True

        profile = attack_v2.profile_snapshot(agent)
        threshold = profile.threshold
        probe_score = float(genuine_scores[probe_index, sid])
        accepted = probe_score >= threshold
        probe_rejections.append(not accepted)

        matched = np.flatnonzero(
            (y_test != sid) & (session_test == session_id) & (within_test == 10)
        )
        if not len(matched):
            raise ValueError(f"No matched impostor checkpoints for session {session_id}")
        source_rates = []
        for source_id in np.unique(y_test[matched]):
            source_idx = matched[y_test[matched] == source_id]
            source_rates.append(_fraction(impostor_score_matrix[source_idx, sid] >= threshold))
        checkpoint_far = float(np.mean(source_rates))
        checkpoint_fars.append(checkpoint_far)
        checkpoint_rows.append({
            "checkpoint": checkpoint,
            "session": session_id,
            "adaptation_index": adaptation_index,
            "probe_index": probe_index,
            "adaptation_score": adaptation_score,
            "probe_score": probe_score,
            "auth_threshold_before": auth_threshold,
            "update_threshold_before": update_gate,
            "threshold": threshold,
            "mean": profile.mean,
            "sigma": profile.sigma,
            "adaptation_authenticated": int(authenticated),
            "updated": int(updated),
            "accepted": int(accepted),
            "checkpoint_FAR": checkpoint_far,
            "n_impostor_sources": len(source_rates),
            "updates_so_far": updates,
        })

    after = attack_v2.profile_snapshot(agent)
    early_reject, late_reject = split_early_late(probe_rejections)
    early_far_values, late_far_values = split_early_late(checkpoint_fars)
    late_far = float(np.mean(late_far_values))
    early_frr = _fraction(early_reject)
    late_frr = _fraction(late_reject)
    all_impostor_idx = np.flatnonzero(y_test != sid)
    metrics = {
        "early_FRR": early_frr,
        "late_FRR": late_frr,
        "overall_FRR": _fraction(probe_rejections),
        "early_FAR": float(np.mean(early_far_values)),
        "late_FAR": late_far,
        "overall_FAR": float(np.mean(checkpoint_fars)),
        "final_all_FAR": _fraction(impostor_score_matrix[all_impostor_idx, sid] >= after.threshold),
        "FAR": late_far,
        "HTER": 0.5 * (late_frr + late_far),
        "adaptation_attempts": adaptation_attempts,
        "adaptation_accepts": adaptation_accepts,
        "adaptation_auth_rate": adaptation_accepts / adaptation_attempts,
        "genuine_updates": updates,
        "GUR": updates / adaptation_attempts,
        "n_checkpoint_probes": len(probe_rejections),
        "n_early_probes": len(early_reject),
        "n_late_probes": len(late_reject),
        "n_checkpoint_sessions": len(checkpoint_fars),
        "non_stricter_gate_states": non_stricter_gate_states,
        "mu_enroll": mu_enroll,
        **guard.profile_fields(before, after),
    }
    return metrics, checkpoint_rows


def assert_clean_oracle_matches_blind(rows: list[dict], atol: float = 1e-12) -> None:
    blind = next(row for row in rows if row["policy_id"] == "blind")
    oracle = next(row for row in rows if row["policy_id"] == "oracle")
    fields = [
        "early_FRR", "late_FRR", "overall_FRR", "early_FAR", "late_FAR",
        "overall_FAR", "final_all_FAR", "HTER", "GUR",
        "genuine_updates", "mean_after", "sigma_after", "threshold_after",
    ]
    failed = [
        field for field in fields
        if not np.isclose(float(blind[field]), float(oracle[field]), atol=atol, rtol=0)
    ]
    if failed:
        raise AssertionError("Oracle and Blind diverged in genuine-only stream: " + ", ".join(failed))


def assert_clean_lambda_zero_matches_blind(blind: dict, guarded_zero: dict,
                                           atol: float = 1e-12) -> None:
    fields = [
        "early_FRR", "late_FRR", "overall_FRR", "early_FAR", "late_FAR",
        "overall_FAR", "final_all_FAR", "HTER", "GUR", "genuine_updates",
        "mean_after", "sigma_after", "threshold_after",
    ]
    failed = [
        field for field in fields
        if not np.isclose(float(blind[field]), float(guarded_zero[field]), atol=atol, rtol=0)
    ]
    if failed:
        raise AssertionError("Guarded lambda=0 diverged from Blind: " + ", ".join(failed))


def add_frozen_gains(frame: pd.DataFrame) -> pd.DataFrame:
    keys = ["fold", "scenario", "D", "sid"]
    frozen = (
        frame[frame["policy_id"] == "frozen"]
        .set_index(keys)[["late_FRR", "HTER"]]
        .rename(columns={"late_FRR": "frozen_late_FRR", "HTER": "frozen_HTER"})
    )
    out = frame.join(frozen, on=keys)
    if out[["frozen_late_FRR", "frozen_HTER"]].isna().any().any():
        raise AssertionError("Missing paired Frozen row")
    out["adaptation_gain"] = out["frozen_late_FRR"] - out["late_FRR"]
    out["hter_gain"] = out["frozen_HTER"] - out["HTER"]
    frozen_early = (
        frame[frame["policy_id"] == "frozen"]
        .set_index(keys)["early_FRR"]
        .rename("frozen_early_FRR")
    )
    out = out.join(frozen_early, on=keys)
    out["recovery_DiD"] = (
        (out["early_FRR"] - out["late_FRR"])
        - (out["frozen_early_FRR"] - out["frozen_late_FRR"])
    )
    return out


def percentage_export(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    columns = [
        column for column in out.columns
        if column in RATE_COLUMNS
        or (column.endswith("_subject_sd") and column.removesuffix("_subject_sd") in RATE_COLUMNS)
    ]
    out[columns] = 100.0 * out[columns]
    return out


def numeric_metrics(frame: pd.DataFrame, excluded: Iterable[str]) -> list[str]:
    excluded = set(excluded)
    return [
        column for column in frame.select_dtypes(include=[np.number]).columns
        if column not in excluded
    ]


def aggregate_by_fold(subject_fold: pd.DataFrame) -> pd.DataFrame:
    keys = ["fold", "scenario", "D", "policy_id", "method", "lambda", "lambda_value"]
    metrics = numeric_metrics(subject_fold, keys + ["sid"])
    means = subject_fold.groupby(keys, as_index=False, dropna=False)[metrics].mean()
    counts = subject_fold.groupby(keys, as_index=False, dropna=False).agg(
        n_subjects=("sid", "nunique")
    )
    return means.merge(counts, on=keys).sort_values(keys)


def aggregate_by_subject(subject_fold: pd.DataFrame) -> pd.DataFrame:
    keys = ["scenario", "D", "policy_id", "method", "lambda", "lambda_value", "sid"]
    metrics = numeric_metrics(subject_fold, keys + ["fold"])
    means = subject_fold.groupby(keys, as_index=False, dropna=False)[metrics].mean()
    counts = subject_fold.groupby(keys, as_index=False, dropna=False).agg(
        n_folds=("fold", "nunique")
    )
    return means.merge(counts, on=keys).sort_values(keys)


def make_summary(by_subject: pd.DataFrame) -> pd.DataFrame:
    keys = ["scenario", "D", "policy_id", "method", "lambda", "lambda_value"]
    metrics = numeric_metrics(by_subject, keys + ["sid", "n_folds"])
    mean = by_subject.groupby(keys, as_index=False, dropna=False)[metrics].mean()
    sd = by_subject.groupby(keys, as_index=False, dropna=False)[metrics].std(ddof=1)
    sd = sd.rename(columns={column: f"{column}_subject_sd" for column in metrics})
    counts = by_subject.groupby(keys, as_index=False, dropna=False).agg(
        n_subjects=("sid", "nunique")
    )
    return mean.merge(sd, on=keys).merge(counts, on=keys).sort_values(keys)


def paired_subject_bootstrap(
    by_subject: pd.DataFrame,
    n_bootstrap: int,
    seed: int,
) -> pd.DataFrame:
    """Bootstrap paired subject effects after averaging each subject over folds."""
    effects = {
        "late_FRR_gain": ("late_FRR", -1.0),
        "HTER_gain": ("HTER", -1.0),
        "late_FAR_change": ("late_FAR", 1.0),
        "GUR_change": ("GUR", 1.0),
    }
    rows: list[dict] = []
    for (scenario, drift), group in by_subject.groupby(["scenario", "D"], sort=True):
        frozen = group[group["policy_id"] == "frozen"].set_index("sid")
        for identity, method_group in group[group["policy_id"] != "frozen"].groupby(
            ["policy_id", "method", "lambda", "lambda_value"], dropna=False, sort=True
        ):
            policy_id, method, lambda_label, lambda_value = identity
            method_frame = method_group.set_index("sid")
            common = frozen.index.intersection(method_frame.index)
            if len(common) < 2:
                continue
            for effect_name, (metric, direction) in effects.items():
                if direction < 0:
                    differences = frozen.loc[common, metric].to_numpy() - method_frame.loc[common, metric].to_numpy()
                else:
                    differences = method_frame.loc[common, metric].to_numpy() - frozen.loc[common, metric].to_numpy()
                # Reuse the same resampling indices across scenarios for the
                # same D/policy/effect.  Claimant-only and global genuine paths
                # are identical, so their genuine-effect intervals should be
                # identical rather than differ from bootstrap Monte Carlo noise.
                seed_material = f"{seed}|{drift:.6f}|{policy_id}|{effect_name}".encode()
                draw_seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "little")
                rng = np.random.default_rng(draw_seed)
                draws = rng.choice(
                    differences, size=(n_bootstrap, len(differences)), replace=True
                ).mean(axis=1)
                rows.append({
                    "scenario": scenario, "D": drift, "policy_id": policy_id,
                    "method": method, "lambda": lambda_label,
                    "lambda_value": lambda_value, "effect": effect_name,
                    "n_subjects": len(differences), "n_bootstrap": n_bootstrap,
                    "estimate": float(differences.mean()),
                    "ci95_low": float(np.quantile(draws, 0.025)),
                    "ci95_high": float(np.quantile(draws, 0.975)),
                })
    return pd.DataFrame(rows)


def save_trajectory_plots(checkpoints: pd.DataFrame, output_dir: Path) -> None:
    """Save aggregate claimant-only trajectories that expose update selection."""
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    methods = ["Frozen", "Blind EMA", "Guarded EMA", "Oracle-all-genuine"]
    colors = {
        "Frozen": "#4b5563",
        "Blind EMA": "#d97706",
        "Guarded EMA": "#2563eb",
        "Oracle-all-genuine": "#059669",
    }
    claimant = checkpoints[checkpoints["scenario"] == "claimant_only"].copy()
    path_keys = ["fold", "D", "sid", "policy_id"]
    claimant["path_length"] = claimant.groupby(path_keys)["checkpoint"].transform("size")
    # Plot only complete five-checkpoint paths.  Without this restriction the
    # fifth ordinal point comes from a smaller set of folds/subjects and creates
    # a cohort-composition artifact that can look like causal late drift.
    claimant = claimant[claimant["path_length"] == 5]
    for drift, frame in claimant.groupby("D", sort=True):
        n_paths = frame[["fold", "sid"]].drop_duplicates().shape[0]
        grouped = frame.groupby(["method", "checkpoint"], as_index=False).agg(
            adaptation_score=("adaptation_score", "mean"),
            probe_score=("probe_score", "mean"),
            threshold=("threshold", "mean"),
            mean=("mean", "mean"),
            sigma=("sigma", "mean"),
            auth_rate=("adaptation_authenticated", "mean"),
            update_rate=("updated", "mean"),
        )
        score_path = frame.groupby("checkpoint", as_index=False).agg(
            adaptation_score=("adaptation_score", "mean"),
            probe_score=("probe_score", "mean"),
        )
        fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)

        ax = axes[0, 0]
        x = score_path["checkpoint"] + 1
        ax.plot(x, score_path["adaptation_score"], color="#111827", marker="o",
                linewidth=2.2, label="Genuine adaptation score")
        ax.plot(x, score_path["probe_score"], color="#7c3aed", marker="s",
                linewidth=2.2, label="Genuine checkpoint score")
        for method in methods:
            values = grouped[grouped["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, values["threshold"],
                        color=colors[method], linewidth=1.8,
                        label=f"{method} threshold")
        ax.set(title=f"Scores and authentication thresholds (D={drift:g})",
               xlabel="Session checkpoint", ylabel="LSTM claimant score")
        ax.legend(fontsize=8, ncol=2)

        ax = axes[0, 1]
        for method in methods:
            values = grouped[grouped["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, values["mean"], marker="o",
                        color=colors[method], label=method)
        ax.set(title="EMA profile mean", xlabel="Session checkpoint", ylabel="Mean score")
        ax.legend(fontsize=8)

        ax = axes[1, 0]
        for method in methods:
            values = grouped[grouped["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, values["sigma"], marker="o",
                        color=colors[method], label=method)
        ax.set(title="EMA profile sigma", xlabel="Session checkpoint", ylabel="Sigma")
        ax.legend(fontsize=8)

        ax = axes[1, 1]
        for method in methods:
            values = grouped[grouped["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, 100 * values["auth_rate"],
                        color=colors[method], linestyle="--", linewidth=1.4)
                ax.plot(values["checkpoint"] + 1, 100 * values["update_rate"],
                        color=colors[method], marker="o", linewidth=2,
                        label=f"{method} update")
        ax.set(title="Authentication (dashed) and update rates",
               xlabel="Session checkpoint", ylabel="Rate (%)", ylim=(-2, 102))
        ax.legend(fontsize=8)
        for axis in axes.flat:
            axis.grid(alpha=0.25)
        fig.suptitle(
            f"Claimant-only clean drift trajectories, D={drift:g} "
            f"({n_paths} complete subject-fold paths)",
            fontsize=14,
        )
        fig.savefig(figure_dir / f"trajectory_claimant_only_D{drift:.1f}.png", dpi=180)
        plt.close(fig)


def assert_d0_scenarios_equal(subject_fold: pd.DataFrame) -> None:
    keys = ["fold", "D", "sid", "policy_id"]
    metrics = ["early_FRR", "late_FRR", "late_FAR", "HTER", "GUR", "threshold_delta"]
    global_zero = subject_fold[(subject_fold["scenario"] == "global") & (subject_fold["D"] == 0)].set_index(keys)
    claimant_zero = subject_fold[(subject_fold["scenario"] == "claimant_only") & (subject_fold["D"] == 0)].set_index(keys)
    if not global_zero.index.equals(claimant_zero.index):
        raise AssertionError("D=0 scenario cohorts differ")
    if not np.allclose(global_zero[metrics], claimant_zero[metrics], atol=0, rtol=0):
        raise AssertionError("Global and claimant-only D=0 sanity check failed")


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
    return Path("results") / f"{datetime.now():%Y%m%d-%H%M%S}-guarded-drift"


def run(args: argparse.Namespace) -> Path:
    source_dir = Path(args.source_dir).resolve()
    cache_dir = Path(args.cache_dir).resolve() if args.cache_dir else source_dir / "paper3_cache"
    output_dir = resolve_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    core, attack_v2 = guard.load_canonical_modules(source_dir)
    policy_grid = guard.policies(args.lambdas)
    policy_grid.insert(3, guard.Policy("oracle_all", "Oracle-all-genuine", -1.0))
    n_folds = int(getattr(core, "N_FOLDS", 5))
    rows: list[dict] = []
    checkpoints: list[dict] = []
    exclusions: list[dict] = []
    log: list[str] = []

    config = {
        "source_dir": str(source_dir), "cache_dir": str(cache_dir),
        "drifts": list(args.drifts), "scenarios": ["global", "claimant_only"],
        "lambdas": list(args.lambdas), "bootstrap_replicates": args.bootstrap_replicates,
        "bootstrap_seed": args.seed,
        "genuine_roles": "per session within=0 adaptation, within=10 probe checkpoint",
        "far_definition": "source-macro FAR at temporally matched checkpoint sessions",
        "hter_definition": "0.5 * (late_FRR + late_FAR)",
        "adaptation_gain_definition": "Frozen late_FRR - method late_FRR",
        "statistical_unit": "subject after averaging folds",
        "oracle_all_definition": "force canonical EMA update for every genuine candidate",
        "bootstrap_cohorts": ["all_available_folds", "complete_case_5_folds"],
    }
    (output_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    status = "running"

    try:
        for fold in range(1, n_folds + 1):
            clean = attack_v2.load_fold(cache_dir, fold, drift=0.0)
            val_scores, y_val = clean["val_scores"], clean["y_val"]
            y_test = clean["y_test"]
            session_test, within_test = clean["session_test"], clean["within_test"]
            clean_scores = clean["test_scores"]
            for drift in args.drifts:
                drifted = attack_v2.load_fold(cache_dir, fold, drift=drift)
                for field in ("y_test", "session_test", "within_test"):
                    if not np.array_equal(clean[field], drifted[field]):
                        raise AssertionError(f"Cache alignment failed for fold={fold}, D={drift}, {field}")
                drift_scores = drifted["test_scores"]
                for sid in range(drift_scores.shape[1]):
                    enrollment = np.asarray(val_scores[y_val == sid, sid], dtype=float)
                    validation_impostor = np.asarray(val_scores[y_val != sid, sid], dtype=float)
                    genuine_idx = core.chronology_order(
                        session_test, within_test, np.flatnonzero(y_test == sid)
                    )
                    impostor_idx = np.flatnonzero(y_test != sid)
                    if len(enrollment) < 2 or not len(validation_impostor) or len(genuine_idx) < 4:
                        exclusions.append({"fold": fold, "D": drift, "sid": sid,
                                           "reason": "insufficient enrollment/validation/genuine observations"})
                        continue
                    try:
                        session_pairs(genuine_idx, session_test, within_test)
                    except ValueError as exc:
                        exclusions.append({"fold": fold, "D": drift, "sid": sid,
                                           "reason": str(exc)})
                        continue
                    _, tau0 = core.eer_from_scores(enrollment, validation_impostor)
                    for scenario in ("global", "claimant_only"):
                        impostor_matrix = drift_scores if scenario == "global" else clean_scores
                        condition_rows: list[dict] = []
                        for policy in policy_grid:
                            metrics, probe_rows = evaluate_subject_policy(
                                policy=policy, sid=sid, tau0=float(tau0),
                                enrollment=enrollment,
                                chronological_genuine=genuine_idx,
                                genuine_scores=drift_scores,
                                impostor_score_matrix=impostor_matrix,
                                y_test=y_test, session_test=session_test,
                                within_test=within_test,
                                core=core, attack_v2=attack_v2,
                            )
                            identity = {
                                "fold": fold, "scenario": scenario, "D": float(drift),
                                "sid": sid, "policy_id": policy.policy_id,
                                "method": policy.method, "lambda": policy.lambda_label,
                                "lambda_value": policy.lambda_value, "tau0": float(tau0),
                            }
                            row = {**identity, **metrics}
                            rows.append(row)
                            condition_rows.append(row)
                            checkpoints.extend({**identity, **probe} for probe in probe_rows)
                        assert_clean_oracle_matches_blind(condition_rows)
                        blind_metrics = next(row for row in condition_rows if row["policy_id"] == "blind")
                        if any(np.isclose(value, 0.0) for value in args.lambdas):
                            zero_metrics = next(
                                row for row in condition_rows if row["policy_id"] == "guarded_0.00"
                            )
                        else:
                            zero_policy = guard.Policy("guarded_0.00", "Guarded EMA", 0.0)
                            zero_metrics, _ = evaluate_subject_policy(
                                policy=zero_policy, sid=sid, tau0=float(tau0),
                                enrollment=enrollment,
                                chronological_genuine=genuine_idx,
                                genuine_scores=drift_scores,
                                impostor_score_matrix=impostor_matrix,
                                y_test=y_test, session_test=session_test,
                                within_test=within_test,
                                core=core, attack_v2=attack_v2,
                            )
                        assert_clean_lambda_zero_matches_blind(blind_metrics, zero_metrics)

            message = f"Fold {fold}/{n_folds} complete"
            log.append(message)
            print(message, flush=True)

        subject_fold = add_frozen_gains(pd.DataFrame(rows))
        assert_d0_scenarios_equal(subject_fold)
        by_fold = aggregate_by_fold(subject_fold)
        by_subject = aggregate_by_subject(subject_fold)
        summary = make_summary(by_subject)
        bootstrap_all = paired_subject_bootstrap(
            by_subject, n_bootstrap=args.bootstrap_replicates, seed=args.seed
        )
        bootstrap_all.insert(0, "cohort", "all_available_folds")
        complete_subjects = by_subject.groupby("sid")["n_folds"].min()
        complete_ids = complete_subjects[complete_subjects == n_folds].index
        complete_case = by_subject[by_subject["sid"].isin(complete_ids)]
        bootstrap_complete = paired_subject_bootstrap(
            complete_case, n_bootstrap=args.bootstrap_replicates, seed=args.seed
        )
        bootstrap_complete.insert(0, "cohort", "complete_case_5_folds")
        bootstrap = pd.concat([bootstrap_all, bootstrap_complete], ignore_index=True)

        percentage_export(subject_fold).to_csv(output_dir / "paper3_guarded_drift_subject_fold.csv", index=False)
        percentage_export(by_fold).to_csv(output_dir / "paper3_guarded_drift_by_fold_descriptive.csv", index=False)
        percentage_export(by_subject).to_csv(output_dir / "paper3_guarded_drift_by_subject.csv", index=False)
        percentage_export(summary).to_csv(output_dir / "paper3_guarded_drift_summary.csv", index=False)
        checkpoint_frame = pd.DataFrame(checkpoints)
        percentage_export(checkpoint_frame).to_csv(
            output_dir / "paper3_guarded_drift_checkpoints.csv", index=False
        )
        save_trajectory_plots(checkpoint_frame, output_dir)
        bootstrap_export = bootstrap.copy()
        bootstrap_export[["estimate", "ci95_low", "ci95_high"]] *= 100.0
        bootstrap_export.to_csv(output_dir / "paper3_guarded_drift_paired_bootstrap.csv", index=False)
        pd.DataFrame(exclusions, columns=["fold", "D", "sid", "reason"]).to_csv(
            output_dir / "exclusions.csv", index=False
        )

        key = percentage_export(summary)
        display_columns = [
            "scenario", "D", "method", "lambda", "early_FRR", "late_FRR",
            "late_FAR", "HTER", "GUR", "threshold_delta", "adaptation_gain",
        ]
        display = key[display_columns]
        print("\nClean-drift summary (subject macro means):")
        print(display.round(5).to_string(index=False))
        log.append("\n" + display.round(5).to_string(index=False))
        status = "complete"
        return output_dir
    finally:
        (output_dir / "run.log").write_text("\n".join(log) + "\n", encoding="utf-8")
        manifest = {
            "status": status, "created_utc": datetime.now(timezone.utc).isoformat(),
            "command": shlex.join(sys.argv), "python": sys.version,
            "platform": platform.platform(),
            "source_hashes": {
                "hmog_revised_experiment.py": sha256(source_dir / "hmog_revised_experiment.py"),
                "paper3_poisoning_attack_v2.py": sha256(source_dir / "paper3_poisoning_attack_v2.py"),
                "paper3_guarded_adaptation.py": sha256(Path(guard.__file__).resolve()),
                "paper3_guarded_drift.py": sha256(Path(__file__).resolve()),
            },
            "cache_hashes": {
                path.name: sha256(path)
                for path in sorted(cache_dir.glob("fold*.npz"))
                if path.name.endswith("_base.npz")
                or any(path.name.endswith(f"D{drift:.1f}.npz") for drift in args.drifts)
            },
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=".")
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--drifts", type=parse_drifts, default=DEFAULT_DRIFTS)
    parser.add_argument("--lambdas", type=parse_lambdas, default=DEFAULT_LAMBDAS)
    parser.add_argument("--bootstrap-replicates", type=int, default=DEFAULT_BOOTSTRAPS)
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    if args.bootstrap_replicates < 100:
        parser.error("--bootstrap-replicates must be at least 100")
    return args


if __name__ == "__main__":
    destination = run(parse_args())
    print(f"\nSaved guarded clean-drift run: {destination.resolve()}")
