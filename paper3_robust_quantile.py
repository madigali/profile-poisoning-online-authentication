#!/usr/bin/env python3
"""Adaptive Quantile Profile diagnostic under clean claimant-only drift.

The experiment changes the score-profile state while preserving the initial
validation-EER operating point.  Accepted-only and Oracle-all Quantile use the
same weighted q20/q50 representation and memory parameter; only their available
feedback differs.  All fold-specific rho values are selected from validation
scores before any outer test cache is loaded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import paper3_guarded_adaptation as guard
import paper3_guarded_drift as drift
import paper3_temporal_recovery as tq


DEFAULT_RHOS = (0.80, 0.90, 0.95)
DEFAULT_DRIFTS = (0.0, 1.0, 2.0)
DEFAULT_BOOTSTRAPS = 10_000
Q_LOW = 0.20
Q_CENTER = 0.50
MIN_INITIAL_SPAN = 1e-8
VALIDATION_FAR_LIMIT = 0.01
VALIDATION_HTER_LIMIT = 0.005
RATE_COLUMNS = set(drift.RATE_COLUMNS) | {
    "update_rate", "late_FRR_gain", "late_FAR_change", "HTER_change",
    "censoring_FRR_cost", "censoring_FAR_change", "censoring_HTER_cost",
    "frozen_late_FRR", "frozen_late_FAR", "frozen_HTER",
}


class InvalidQuantilePath(ValueError):
    """Enrollment q50-q20 is too small for the frozen threshold mapping."""


class ValidationSelectionFailure(RuntimeError):
    """At least one fold lacks a feasible Accepted-only Quantile rho."""


@dataclass(frozen=True)
class QuantileSnapshot:
    q20: float
    q50: float
    threshold: float
    scores: tuple[float, ...]
    weights: tuple[float, ...]


def weighted_quantile(scores: np.ndarray, weights: np.ndarray, probability: float) -> float:
    """Discrete inverse weighted CDF; deliberately no interpolation."""
    values = np.asarray(scores, dtype=float)
    mass = np.asarray(weights, dtype=float)
    if values.ndim != 1 or mass.ndim != 1 or len(values) != len(mass) or not len(values):
        raise ValueError("scores and weights must be non-empty one-dimensional arrays")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(mass)):
        raise ValueError("scores and weights must be finite")
    if np.any(mass < 0.0) or float(mass.sum()) <= 0.0:
        raise ValueError("weights must be nonnegative with positive sum")
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    sorted_mass = mass[order] / float(mass.sum())
    cumulative = np.cumsum(sorted_mass)
    index = int(np.searchsorted(cumulative, probability, side="left"))
    return float(sorted_values[min(index, len(sorted_values) - 1)])


class AdaptiveQuantileProfile:
    def __init__(self, enrollment: np.ndarray, tau0: float, rho: float):
        enrollment = np.asarray(enrollment, dtype=float)
        if enrollment.ndim != 1 or len(enrollment) < 2:
            raise ValueError("quantile enrollment requires at least two scores")
        if not np.all(np.isfinite(enrollment)):
            raise ValueError("enrollment scores must be finite")
        if not 0.0 < rho < 1.0:
            raise ValueError("rho must lie strictly between 0 and 1")
        self.scores = enrollment.copy()
        self.weights = np.full(len(enrollment), 1.0 / len(enrollment), dtype=float)
        self.rho = float(rho)
        self.tau0 = float(tau0)
        self.q20_0 = weighted_quantile(self.scores, self.weights, Q_LOW)
        self.q50_0 = weighted_quantile(self.scores, self.weights, Q_CENTER)
        self.initial_span = self.q50_0 - self.q20_0
        if self.initial_span < MIN_INITIAL_SPAN:
            raise InvalidQuantilePath(
                f"q50_0 - q20_0={self.initial_span:.12g} < {MIN_INITIAL_SPAN:g}"
            )
        self.c = (self.q50_0 - self.tau0) / self.initial_span
        if not np.isfinite(self.c):
            raise InvalidQuantilePath("non-finite threshold mapping coefficient c")
        if not np.isclose(self.threshold, self.tau0, atol=1e-12, rtol=0.0):
            raise AssertionError("Quantile profile failed initial-threshold equivalence")

    @property
    def q20(self) -> float:
        return weighted_quantile(self.scores, self.weights, Q_LOW)

    @property
    def q50(self) -> float:
        return weighted_quantile(self.scores, self.weights, Q_CENTER)

    @property
    def threshold(self) -> float:
        return float(self.q50 - self.c * (self.q50 - self.q20))

    def update(self, score: float) -> None:
        score = float(score)
        if not np.isfinite(score):
            raise ValueError("update score must be finite")
        self.weights = self.rho * self.weights
        self.scores = np.append(self.scores, score)
        self.weights = np.append(self.weights, 1.0 - self.rho)
        self.weights = self.weights / float(self.weights.sum())

    def snapshot(self) -> QuantileSnapshot:
        return QuantileSnapshot(
            q20=self.q20, q50=self.q50, threshold=self.threshold,
            scores=tuple(map(float, self.scores)),
            weights=tuple(map(float, self.weights)),
        )


def process_quantile_score(profile: AdaptiveQuantileProfile, score: float,
                           *, oracle_all: bool) -> dict[str, float | int]:
    score = float(score)
    threshold_before = profile.threshold
    q20_before, q50_before = profile.q20, profile.q50
    authenticated = score >= threshold_before
    updated = bool(authenticated or oracle_all)
    if updated:
        profile.update(score)
    return {
        "authenticated": int(authenticated), "updated": int(updated),
        "threshold_before": threshold_before, "threshold_after": profile.threshold,
        "q20_before": q20_before, "q20_after": profile.q20,
        "q50_before": q50_before, "q50_after": profile.q50,
    }


def evaluate_quantile_pairs(
    rho: float,
    oracle_all: bool,
    sid: int,
    tau0: float,
    enrollment: np.ndarray,
    pairs: Sequence[tuple[int, int, int]],
    genuine_scores: np.ndarray,
    impostor_score_matrix: np.ndarray,
    y: np.ndarray,
    session: np.ndarray,
    within: np.ndarray,
) -> tuple[dict, list[dict], list[dict]]:
    profile = AdaptiveQuantileProfile(enrollment, tau0, rho)
    before = profile.snapshot()
    rejections: list[bool] = []
    fars: list[float] = []
    checkpoints: list[dict] = []
    source_rows: list[dict] = []
    auth_count = update_count = 0

    for checkpoint, (session_id, adaptation_index, probe_index) in enumerate(pairs):
        adaptation_score = float(genuine_scores[adaptation_index, sid])
        event = process_quantile_score(profile, adaptation_score, oracle_all=oracle_all)
        auth_count += int(event["authenticated"])
        update_count += int(event["updated"])
        probe_score = float(genuine_scores[probe_index, sid])
        accepted = probe_score >= profile.threshold
        rejections.append(not accepted)
        far, source_values = tq.source_macro_far(
            impostor_score_matrix, sid, profile.threshold, y, session, within,
            session_id,
        )
        fars.append(far)
        for source_id, rate, denominator in source_values:
            source_rows.append({
                "checkpoint": checkpoint, "session": session_id,
                "source_id": source_id, "source_FAR": rate,
                "source_probe_n": denominator,
            })
        checkpoints.append({
            "checkpoint": checkpoint, "session": session_id,
            "adaptation_index": adaptation_index, "probe_index": probe_index,
            "adaptation_score": adaptation_score, "probe_score": probe_score,
            "auth_threshold_before": event["threshold_before"],
            "threshold": profile.threshold, "q20": profile.q20, "q50": profile.q50,
            "adaptation_authenticated": event["authenticated"],
            "updated": event["updated"], "accepted": int(accepted),
            "checkpoint_FAR": far, "n_impostor_sources": len(source_values),
            "updates_so_far": update_count,
        })

    after = profile.snapshot()
    early_reject, late_reject = tq.endpoint_split(rejections)
    early_far, late_far = tq.endpoint_split(fars)
    attempts = len(pairs)
    metrics = {
        "early_FRR": float(np.mean(early_reject)),
        "late_FRR": float(np.mean(late_reject)),
        "overall_FRR": float(np.mean(rejections)),
        "early_FAR": float(np.mean(early_far)),
        "late_FAR": float(np.mean(late_far)),
        "overall_FAR": float(np.mean(fars)),
        "final_all_FAR": float(np.mean(
            impostor_score_matrix[np.flatnonzero(y != sid), sid] >= after.threshold
        )),
        "FAR": float(np.mean(late_far)),
        "HTER": 0.5 * (float(np.mean(late_reject)) + float(np.mean(late_far))),
        "adaptation_attempts": attempts, "adaptation_accepts": auth_count,
        "adaptation_auth_rate": auth_count / attempts,
        "genuine_updates": update_count, "GUR": update_count / attempts,
        "update_rate": update_count / attempts,
        "n_checkpoint_probes": attempts, "n_early_probes": len(early_reject),
        "n_late_probes": len(late_reject), "n_checkpoint_sessions": attempts,
        "rho": float(rho), "c": profile.c, "initial_quantile_span": profile.initial_span,
        "q20_before": before.q20, "q20_after": after.q20,
        "q20_delta": after.q20 - before.q20,
        "q50_before": before.q50, "q50_after": after.q50,
        "q50_delta": after.q50 - before.q50,
        "threshold_before": before.threshold, "threshold_after": after.threshold,
        "threshold_delta": after.threshold - before.threshold,
    }
    return metrics, checkpoints, source_rows


def select_rho(summary: pd.DataFrame) -> pd.Series:
    frame = summary.copy()
    frame["feasible"] = (
        (frame["late_FAR_change"] <= VALIDATION_FAR_LIMIT + 1e-12)
        & (frame["HTER_change"] <= VALIDATION_HTER_LIMIT + 1e-12)
    )
    feasible = frame[frame["feasible"]]
    if not len(feasible):
        raise RuntimeError(
            "No Accepted-only Quantile rho satisfies validation Delta-FAR <= +1pp "
            "and HTER degradation <= +0.5pp"
        )
    selected = feasible.sort_values(
        ["late_FRR_gain", "rho"], ascending=[False, False], kind="mergesort"
    ).iloc[0].copy()
    selected["selection_status"] = "feasible"
    return selected


def tune_fold(fold: int, cache_dir: Path, core, max_subjects: int | None):
    payload = tq.load_validation_payload(cache_dir, fold)
    drift_scores, drift_seed = tq.load_validation_drift_scores(
        core, cache_dir, fold, tq.VALIDATION_DRIFT
    )
    clean_scores = payload["val_scores"].astype(np.float64)
    y, session, within = payload["y_val"], payload["session_val"], payload["within_val"]
    rows: list[dict] = []
    c_rows: list[dict] = []
    exclusions: list[dict] = []
    n_subjects = clean_scores.shape[1]
    subject_ids = range(n_subjects if max_subjects is None else min(max_subjects, n_subjects))

    for sid in subject_ids:
        own = np.flatnonzero(y == sid)
        try:
            pairs = drift.session_pairs(own, session, within)
        except ValueError as exc:
            exclusions.append({"fold": fold, "sid": sid, "reason": str(exc)})
            continue
        enrollment = np.asarray(clean_scores[own, sid], dtype=float)
        validation_impostor = np.asarray(clean_scores[y != sid, sid], dtype=float)
        _, tau0 = core.eer_from_scores(enrollment, validation_impostor)
        try:
            diagnostic = AdaptiveQuantileProfile(enrollment, float(tau0), DEFAULT_RHOS[0])
        except InvalidQuantilePath as exc:
            exclusions.append({
                "fold": fold, "sid": sid,
                "reason": f"invalid_quantile_path: {exc}",
            })
            continue
        c_rows.append({
            "fold": fold, "sid": sid, "tau0": float(tau0), "c": diagnostic.c,
            "q20_0": diagnostic.q20_0, "q50_0": diagnostic.q50_0,
            "initial_quantile_span": diagnostic.initial_span,
        })
        frozen = tq.frozen_pair_metrics(
            sid, float(tau0), pairs, drift_scores, clean_scores, y, session, within
        )
        for rho in DEFAULT_RHOS:
            for oracle_all, policy_id, method in [
                (False, "quantile_accepted", "Accepted-only Quantile"),
                (True, "quantile_oracle", "Oracle-all Quantile"),
            ]:
                metrics, _, _ = evaluate_quantile_pairs(
                    rho, oracle_all, sid, float(tau0), enrollment, pairs,
                    drift_scores, clean_scores, y, session, within,
                )
                rows.append({
                    "fold": fold, "sid": sid, "policy_id": policy_id,
                    "method": method, "rho": rho,
                    "late_FRR": metrics["late_FRR"], "late_FAR": metrics["late_FAR"],
                    "HTER": metrics["HTER"], "GUR": metrics["GUR"],
                    "adaptation_auth_rate": metrics["adaptation_auth_rate"],
                    "q20_delta": metrics["q20_delta"], "q50_delta": metrics["q50_delta"],
                    "threshold_delta": metrics["threshold_delta"],
                    "frozen_late_FRR": frozen["late_FRR"],
                    "frozen_late_FAR": frozen["late_FAR"],
                    "frozen_HTER": frozen["HTER"],
                    "late_FRR_gain": frozen["late_FRR"] - metrics["late_FRR"],
                    "late_FAR_change": metrics["late_FAR"] - frozen["late_FAR"],
                    "HTER_change": metrics["HTER"] - frozen["HTER"],
                })

    subject_frame = pd.DataFrame(rows)
    if subject_frame.empty:
        raise RuntimeError(f"Fold {fold}: no valid quantile paths")
    keys = ["policy_id", "method", "rho"]
    metrics = [
        "late_FRR", "late_FAR", "HTER", "GUR", "adaptation_auth_rate",
        "q20_delta", "q50_delta", "threshold_delta", "frozen_late_FRR",
        "frozen_late_FAR", "frozen_HTER", "late_FRR_gain",
        "late_FAR_change", "HTER_change",
    ]
    summary = subject_frame.groupby(keys, as_index=False)[metrics].mean()
    counts = subject_frame.groupby(keys, as_index=False).agg(n_subjects=("sid", "nunique"))
    summary = summary.merge(counts, on=keys)
    summary.insert(0, "fold", fold)
    accepted = summary[summary["policy_id"] == "quantile_accepted"]
    try:
        selected = select_rho(accepted)
    except RuntimeError:
        diagnostic = accepted.sort_values(
            ["late_FRR_gain", "rho"], ascending=[False, False], kind="mergesort"
        ).iloc[0]
        metadata = {
            "fold": fold, "selection_status": "no_feasible_rho",
            "selected_rho": float("nan"),
            "best_unconstrained_rho": float(diagnostic["rho"]),
            "best_unconstrained_late_FRR_gain": float(diagnostic["late_FRR_gain"]),
            "best_unconstrained_late_FAR_change": float(diagnostic["late_FAR_change"]),
            "best_unconstrained_HTER_change": float(diagnostic["HTER_change"]),
            "n_feasible_rhos": 0, "validation_drift_seed": drift_seed,
            "n_validation_subjects": int(diagnostic["n_subjects"]),
            "n_validation_exclusions": len(exclusions),
        }
        return None, subject_frame, summary, pd.DataFrame(c_rows), {
            "metadata": metadata, "exclusions": exclusions,
        }
    metadata = {
        "fold": fold, "selection_status": "feasible",
        "selected_rho": float(selected["rho"]),
        "selected_validation_late_FRR_gain": float(selected["late_FRR_gain"]),
        "selected_validation_late_FAR_change": float(selected["late_FAR_change"]),
        "selected_validation_HTER_change": float(selected["HTER_change"]),
        "n_feasible_rhos": int((
            (accepted["late_FAR_change"] <= VALIDATION_FAR_LIMIT + 1e-12)
            & (accepted["HTER_change"] <= VALIDATION_HTER_LIMIT + 1e-12)
        ).sum()),
        "validation_drift_seed": drift_seed,
        "n_validation_subjects": int(selected["n_subjects"]),
        "n_validation_exclusions": len(exclusions),
    }
    return float(selected["rho"]), subject_frame, summary, pd.DataFrame(c_rows), {
        "metadata": metadata, "exclusions": exclusions,
    }


def percentage_export(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    selected_rates = {
        "selected_validation_late_FRR_gain", "selected_validation_late_FAR_change",
        "selected_validation_HTER_change", "best_unconstrained_late_FRR_gain",
        "best_unconstrained_late_FAR_change", "best_unconstrained_HTER_change",
    }
    columns = [
        column for column in out.columns
        if column in RATE_COLUMNS
        or (column.endswith("_subject_sd") and column.removesuffix("_subject_sd") in RATE_COLUMNS)
        or column in selected_rates
    ]
    if columns:
        out[columns] = 100.0 * out[columns]
    return out


def feedback_contrast_table(validation_summary: pd.DataFrame) -> pd.DataFrame:
    """Pair Accepted-only and Oracle-all validation outcomes at identical rho."""
    index = ["fold", "rho"]
    metrics = [
        "late_FRR", "late_FAR", "HTER", "GUR", "adaptation_auth_rate",
        "late_FRR_gain", "late_FAR_change", "HTER_change",
        "q20_delta", "q50_delta", "threshold_delta", "n_subjects",
    ]
    accepted = validation_summary[
        validation_summary["policy_id"] == "quantile_accepted"
    ][index + metrics].copy()
    oracle = validation_summary[
        validation_summary["policy_id"] == "quantile_oracle"
    ][index + metrics].copy()
    paired = accepted.merge(
        oracle, on=index, how="inner", validate="one_to_one",
        suffixes=("_accepted", "_oracle"),
    )
    paired["accepted_feasible"] = (
        (paired["late_FAR_change_accepted"] <= VALIDATION_FAR_LIMIT + 1e-12)
        & (paired["HTER_change_accepted"] <= VALIDATION_HTER_LIMIT + 1e-12)
    )
    paired["censoring_FRR_cost"] = (
        paired["late_FRR_accepted"] - paired["late_FRR_oracle"]
    )
    paired["censoring_FAR_change"] = (
        paired["late_FAR_accepted"] - paired["late_FAR_oracle"]
    )
    paired["censoring_HTER_cost"] = paired["HTER_accepted"] - paired["HTER_oracle"]
    return paired.sort_values(index, kind="mergesort").reset_index(drop=True)


def paired_censoring_bootstrap(by_subject: pd.DataFrame, n_bootstrap: int,
                               seed: int) -> pd.DataFrame:
    rows: list[dict] = []
    for drift_value, group in by_subject.groupby("D", sort=True):
        accepted = group[group["policy_id"] == "quantile_accepted"].set_index("sid")
        oracle = group[group["policy_id"] == "quantile_oracle"].set_index("sid")
        common = accepted.index.intersection(oracle.index)
        for effect, metric in [
            ("censoring_FRR_cost", "late_FRR"),
            ("censoring_FAR_change", "late_FAR"),
            ("censoring_HTER_cost", "HTER"),
        ]:
            differences = accepted.loc[common, metric].to_numpy() - oracle.loc[common, metric].to_numpy()
            material = f"{seed}|{drift_value}|{effect}".encode()
            draw_seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "little")
            rng = np.random.default_rng(draw_seed)
            draws = rng.choice(
                differences, size=(n_bootstrap, len(differences)), replace=True
            ).mean(axis=1)
            rows.append({
                "D": drift_value, "effect": effect, "n_subjects": len(common),
                "n_bootstrap": n_bootstrap, "estimate": float(differences.mean()),
                "ci95_low": float(np.quantile(draws, 0.025)),
                "ci95_high": float(np.quantile(draws, 0.975)),
            })
    return pd.DataFrame(rows)


def save_trajectory_plots(checkpoints: pd.DataFrame, output_dir: Path) -> None:
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    methods = [
        "Frozen", "Blind EMA", "Guarded EMA", "Oracle-all-genuine",
        "Accepted-only Quantile", "Oracle-all Quantile",
    ]
    colors = {
        "Frozen": "#4b5563", "Blind EMA": "#d97706", "Guarded EMA": "#2563eb",
        "Oracle-all-genuine": "#059669", "Accepted-only Quantile": "#be123c",
        "Oracle-all Quantile": "#7c3aed",
    }
    frame = checkpoints.copy()
    frame["path_length"] = frame.groupby(
        ["fold", "D", "sid", "policy_id"]
    )["checkpoint"].transform("size")
    frame = frame[frame["path_length"] == 5]
    for drift_value, group in frame.groupby("D", sort=True):
        aggregate = group.groupby(["method", "checkpoint"], as_index=False).agg(
            adaptation_score=("adaptation_score", "mean"),
            probe_score=("probe_score", "mean"), threshold=("threshold", "mean"),
            q20=("q20", "mean"), q50=("q50", "mean"),
            auth_rate=("adaptation_authenticated", "mean"),
            update_rate=("updated", "mean"),
        )
        score_path = group.groupby("checkpoint", as_index=False).agg(
            adaptation_score=("adaptation_score", "mean"),
            probe_score=("probe_score", "mean"),
        )
        n_paths = group[["fold", "sid"]].drop_duplicates().shape[0]
        fig, axes = plt.subplots(2, 2, figsize=(13, 8.4), constrained_layout=True)
        ax = axes[0, 0]
        x = score_path["checkpoint"] + 1
        ax.plot(x, score_path["adaptation_score"], color="#111827", marker="o",
                linewidth=2.2, label="Genuine adaptation score")
        ax.plot(x, score_path["probe_score"], color="#6d28d9", marker="s",
                linewidth=2.2, label="Genuine checkpoint score")
        for method in methods:
            values = aggregate[aggregate["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, values["threshold"],
                        color=colors[method], linewidth=1.7, label=f"{method} threshold")
        ax.set(title=f"Scores and thresholds (D={drift_value:g})",
               xlabel="Session checkpoint", ylabel="LSTM claimant score")
        ax.legend(fontsize=7.2, ncol=2)
        ax = axes[0, 1]
        for method in ["Accepted-only Quantile", "Oracle-all Quantile"]:
            values = aggregate[aggregate["method"] == method]
            ax.plot(values["checkpoint"] + 1, values["q50"], marker="o",
                    color=colors[method], label=f"{method} q50")
            ax.plot(values["checkpoint"] + 1, values["q20"], marker="s",
                    linestyle="--", color=colors[method], label=f"{method} q20")
        ax.set(title="Quantile state", xlabel="Session checkpoint", ylabel="Score")
        ax.legend(fontsize=7.5)
        ax = axes[1, 0]
        for method in methods:
            values = aggregate[aggregate["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, 100 * values["update_rate"],
                        marker="o", color=colors[method], label=method)
        ax.set(title="Production update rate", xlabel="Session checkpoint",
               ylabel="Rate (%)", ylim=(-2, 102))
        ax.legend(fontsize=7.2)
        ax = axes[1, 1]
        for method in methods:
            values = aggregate[aggregate["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, 100 * values["auth_rate"],
                        marker="o", color=colors[method], label=method)
        ax.set(title="Adaptation-sample authentication rate",
               xlabel="Session checkpoint", ylabel="Rate (%)", ylim=(-2, 102))
        ax.legend(fontsize=7.2)
        for axis in axes.flat:
            axis.grid(alpha=0.25)
        fig.suptitle(
            f"Adaptive Quantile Profile, claimant-only D={drift_value:g} "
            f"({n_paths} complete subject-fold paths)", fontsize=14,
        )
        fig.savefig(figure_dir / f"quantile_trajectory_D{drift_value:.1f}.png", dpi=180)
        plt.close(fig)


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
    return Path("results") / f"{datetime.now():%Y%m%d-%H%M%S}-robust-quantile"


def run(args: argparse.Namespace) -> Path:
    source_dir = Path(args.source_dir).resolve()
    cache_dir = Path(args.cache_dir).resolve() if args.cache_dir else source_dir / "paper3_cache"
    output_dir = resolve_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    core, attack_v2 = guard.load_canonical_modules(source_dir)
    folds = tuple(args.folds)
    config = {
        "source_dir": str(source_dir), "cache_dir": str(cache_dir),
        "folds": list(folds), "max_subjects": args.max_subjects,
        "rhos": list(DEFAULT_RHOS), "q_low": Q_LOW, "q_center": Q_CENTER,
        "minimum_initial_span": MIN_INITIAL_SPAN,
        "weighted_quantile": "minimum observed score with cumulative normalized weight >= p",
        "threshold": "q50 - c*(q50-q20), c frozen to reproduce validation EER tau0",
        "validation_replay": "D=0 validation enrollment/calibration; D=2 claimant replay; D=0 impostors",
        "validation_far_limit": VALIDATION_FAR_LIMIT,
        "validation_hter_degradation_limit": VALIDATION_HTER_LIMIT,
        "outer_inferential_status": "exploratory reuse if validation passes",
        "validation_only": bool(args.validation_only),
        "bootstrap_replicates": args.bootstrap_replicates, "seed": args.seed,
    }
    (output_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    status = "running"
    outer_test_scores_loaded = False
    log: list[str] = []
    try:
        selected_rhos: dict[int, float] = {}
        subject_parts: list[pd.DataFrame] = []
        summary_parts: list[pd.DataFrame] = []
        c_parts: list[pd.DataFrame] = []
        selection_rows: list[dict] = []
        exclusions: list[dict] = []
        failures: list[dict] = []

        for fold in folds:
            selected, subject, summary, c_frame, details = tune_fold(
                fold, cache_dir, core, args.max_subjects
            )
            subject_parts.append(subject)
            summary_parts.append(summary)
            c_parts.append(c_frame)
            selection_rows.append(details["metadata"])
            exclusions.extend({"stage": "validation", **row} for row in details["exclusions"])
            if selected is None:
                failures.append(details["metadata"])
                message = f"Fold {fold}: no feasible Accepted-only Quantile rho"
            else:
                selected_rhos[fold] = selected
                message = f"Fold {fold}: selected rho={selected:.2f} on Accepted-only validation"
            print(message, flush=True)
            log.append(message)

        validation_subject = pd.concat(subject_parts, ignore_index=True)
        validation_summary = pd.concat(summary_parts, ignore_index=True)
        feedback_contrast = feedback_contrast_table(validation_summary)
        c_values = pd.concat(c_parts, ignore_index=True)
        selected_frame = pd.DataFrame(selection_rows)
        percentage_export(validation_subject).to_csv(
            output_dir / "paper3_quantile_validation_subject.csv", index=False
        )
        percentage_export(validation_summary).to_csv(
            output_dir / "paper3_quantile_validation_summary.csv", index=False
        )
        percentage_export(feedback_contrast).to_csv(
            output_dir / "paper3_quantile_feedback_contrast.csv", index=False
        )
        percentage_export(selected_frame).to_csv(
            output_dir / "paper3_quantile_selected_by_fold.csv", index=False
        )
        c_values.to_csv(output_dir / "paper3_quantile_c_values.csv", index=False)
        c_values.groupby("fold", as_index=False).agg(
            n=("c", "size"), c_min=("c", "min"), c_median=("c", "median"),
            c_mean=("c", "mean"), c_max=("c", "max"),
            span_min=("initial_quantile_span", "min"),
        ).to_csv(output_dir / "paper3_quantile_c_summary.csv", index=False)

        if failures:
            payload = {
                "status": "validation_failed",
                "reason": "At least one fold had no feasible Accepted-only Quantile rho",
                "failed_folds": [int(row["fold"]) for row in failures],
                "fold_diagnostics": failures, "outer_test_loaded": False,
            }
            (output_dir / "validation_failure.json").write_text(
                json.dumps(payload, indent=2) + "\n"
            )
            pd.DataFrame(exclusions).to_csv(output_dir / "exclusions.csv", index=False)
            status = "validation_failed"
            raise ValidationSelectionFailure(payload["reason"])

        if args.validation_only:
            payload = {
                "status": "validation_complete",
                "all_folds_feasible": True,
                "selected_rho_by_fold": {
                    str(fold): float(selected_rhos[fold]) for fold in sorted(selected_rhos)
                },
                "outer_test_loaded": False,
                "reason": "Explicit --validation-only stop before outer-test loading.",
            }
            (output_dir / "validation_status.json").write_text(
                json.dumps(payload, indent=2) + "\n"
            )
            pd.DataFrame(exclusions).to_csv(output_dir / "exclusions.csv", index=False)
            message = "Validation passed in every fold; validation-only stop applied."
            print(message, flush=True)
            log.append(message)
            status = "validation_complete"
            return output_dir

        rows: list[dict] = []
        checkpoints: list[dict] = []
        source_far_rows: list[dict] = []
        for fold in folds:
            outer_test_scores_loaded = True
            clean = attack_v2.load_fold(cache_dir, fold, drift=0.0)
            rho = selected_rhos[fold]
            val_scores, y_val = clean["val_scores"], clean["y_val"]
            y_test = clean["y_test"]
            session_test, within_test = clean["session_test"], clean["within_test"]
            clean_scores = clean["test_scores"]
            for drift_value in args.drifts:
                drifted = attack_v2.load_fold(cache_dir, fold, drift=drift_value)
                drift_scores = drifted["test_scores"]
                n_subjects = drift_scores.shape[1]
                subject_ids = range(
                    n_subjects if args.max_subjects is None
                    else min(args.max_subjects, n_subjects)
                )
                for sid in subject_ids:
                    enrollment = np.asarray(val_scores[y_val == sid, sid], dtype=float)
                    validation_impostor = np.asarray(val_scores[y_val != sid, sid], dtype=float)
                    genuine_idx = core.chronology_order(
                        session_test, within_test, np.flatnonzero(y_test == sid)
                    )
                    try:
                        pairs = drift.session_pairs(genuine_idx, session_test, within_test)
                        _, tau0 = core.eer_from_scores(enrollment, validation_impostor)
                        AdaptiveQuantileProfile(enrollment, float(tau0), rho)
                    except (ValueError, InvalidQuantilePath) as exc:
                        exclusions.append({
                            "stage": "outer_paired_quantile", "fold": fold,
                            "D": drift_value, "sid": sid, "reason": str(exc),
                        })
                        continue
                    for policy in tq.baseline_policies():
                        metrics, probe_rows = drift.evaluate_subject_policy(
                            policy, sid, float(tau0), enrollment, genuine_idx,
                            drift_scores, clean_scores, y_test, session_test,
                            within_test, core, attack_v2,
                        )
                        identity = {
                            "fold": fold, "scenario": "claimant_only", "D": float(drift_value),
                            "sid": sid, "policy_id": policy.policy_id,
                            "method": policy.method, "lambda": policy.lambda_label,
                            "lambda_value": policy.lambda_value, "rho": float("nan"),
                            "tau0": float(tau0),
                        }
                        rows.append({**identity, **metrics})
                        checkpoints.extend({**identity, "q20": np.nan, "q50": np.nan, **probe}
                                           for probe in probe_rows)
                        if float(drift_value) == 2.0 and policy.policy_id == "frozen":
                            sources = tq.source_rows_from_checkpoints(
                                probe_rows[-2:], sid, clean_scores, y_test,
                                session_test, within_test,
                            )
                            source_far_rows.extend({**identity, **source} for source in sources)
                    for oracle_all, policy_id, method in [
                        (False, "quantile_accepted", "Accepted-only Quantile"),
                        (True, "quantile_oracle", "Oracle-all Quantile"),
                    ]:
                        metrics, probe_rows, sources = evaluate_quantile_pairs(
                            rho, oracle_all, sid, float(tau0), enrollment, pairs,
                            drift_scores, clean_scores, y_test, session_test, within_test,
                        )
                        identity = {
                            "fold": fold, "scenario": "claimant_only", "D": float(drift_value),
                            "sid": sid, "policy_id": policy_id, "method": method,
                            "lambda": "", "lambda_value": -1.0, "rho": rho,
                            "tau0": float(tau0),
                        }
                        rows.append({**identity, **metrics})
                        checkpoints.extend({**identity, **probe} for probe in probe_rows)
                        if float(drift_value) == 2.0 and not oracle_all:
                            first_late = len(pairs) - 2
                            source_far_rows.extend(
                                {**identity, **source} for source in sources
                                if int(source["checkpoint"]) >= first_late
                            )
            print(f"Fold {fold}: exploratory reused outer evaluation complete", flush=True)

        subject_fold = drift.add_frozen_gains(pd.DataFrame(rows))
        by_fold = drift.aggregate_by_fold(subject_fold)
        by_subject = drift.aggregate_by_subject(subject_fold)
        summary = drift.make_summary(by_subject)
        bootstrap_all = drift.paired_subject_bootstrap(
            by_subject, args.bootstrap_replicates, args.seed
        )
        bootstrap_all.insert(0, "cohort", "all_available_folds")
        complete_ids = by_subject.groupby("sid")["n_folds"].min()
        complete_ids = complete_ids[complete_ids == len(folds)].index
        complete_case = by_subject[by_subject["sid"].isin(complete_ids)]
        bootstrap_complete = drift.paired_subject_bootstrap(
            complete_case, args.bootstrap_replicates, args.seed
        )
        bootstrap_complete.insert(0, "cohort", f"complete_case_{len(folds)}_folds")
        bootstrap = pd.concat([bootstrap_all, bootstrap_complete], ignore_index=True)
        censoring = paired_censoring_bootstrap(
            by_subject, args.bootstrap_replicates, args.seed + 177
        )
        source_frame = pd.DataFrame(source_far_rows)
        # Reuse the generic two-way implementation by presenting Accepted-only
        # Quantile under the expected contrast identifier.
        source_for_bootstrap = source_frame.copy()
        source_for_bootstrap.loc[
            source_for_bootstrap["policy_id"] == "quantile_accepted", "policy_id"
        ] = "tq_ema"
        two_way = tq.two_way_far_bootstrap(
            source_for_bootstrap, args.bootstrap_replicates, args.seed + 911
        )
        two_way["contrast"] = "Accepted-only Quantile minus Frozen late FAR"

        percentage_export(subject_fold).to_csv(output_dir / "paper3_quantile_subject_fold.csv", index=False)
        percentage_export(by_fold).to_csv(output_dir / "paper3_quantile_by_fold.csv", index=False)
        percentage_export(by_subject).to_csv(output_dir / "paper3_quantile_by_subject.csv", index=False)
        percentage_export(summary).to_csv(output_dir / "paper3_quantile_summary.csv", index=False)
        checkpoint_frame = pd.DataFrame(checkpoints)
        percentage_export(checkpoint_frame).to_csv(
            output_dir / "paper3_quantile_checkpoints.csv", index=False
        )
        percentage_export(source_frame).to_csv(
            output_dir / "paper3_quantile_source_far.csv.gz", index=False,
            compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
        )
        bootstrap_export = bootstrap.copy()
        bootstrap_export[["estimate", "ci95_low", "ci95_high"]] *= 100.0
        bootstrap_export.to_csv(output_dir / "paper3_quantile_subject_bootstrap.csv", index=False)
        censoring_export = censoring.copy()
        censoring_export[["estimate", "ci95_low", "ci95_high"]] *= 100.0
        censoring_export.to_csv(output_dir / "paper3_quantile_censoring_bootstrap.csv", index=False)
        two_way_export = two_way.copy()
        two_way_export[["estimate", "ci95_low", "ci95_high"]] *= 100.0
        two_way_export.to_csv(output_dir / "paper3_quantile_two_way_far_bootstrap.csv", index=False)
        pd.DataFrame(exclusions).to_csv(output_dir / "exclusions.csv", index=False)
        if not args.skip_plots:
            save_trajectory_plots(checkpoint_frame, output_dir)
        status = "complete_exploratory_outer_reuse"
        return output_dir
    finally:
        (output_dir / "run.log").write_text("\n".join(log) + "\n")
        source_paths = {
            "hmog_revised_experiment.py": source_dir / "hmog_revised_experiment.py",
            "paper3_poisoning_attack_v2.py": source_dir / "paper3_poisoning_attack_v2.py",
            "paper3_guarded_adaptation.py": Path(guard.__file__).resolve(),
            "paper3_guarded_drift.py": Path(drift.__file__).resolve(),
            "paper3_temporal_recovery.py": Path(tq.__file__).resolve(),
            "paper3_robust_quantile.py": Path(__file__).resolve(),
        }
        cache_hashes = {}
        for fold in folds:
            for suffix in ["base.npz", "model.pt"] + [f"D{x:.1f}.npz" for x in args.drifts]:
                path = cache_dir / f"fold{fold}_{suffix}"
                if path.is_file():
                    cache_hashes[path.name] = sha256(path)
        manifest = {
            "status": status, "created_utc": datetime.now(timezone.utc).isoformat(),
            "outer_test_loaded": outer_test_scores_loaded,
            "command": shlex.join(sys.argv), "python": sys.version,
            "platform": platform.platform(),
            "source_hashes": {
                name: sha256(path) for name, path in source_paths.items() if path.is_file()
            },
            "cache_hashes": cache_hashes,
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=".")
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--drifts", type=drift.parse_drifts, default=DEFAULT_DRIFTS)
    parser.add_argument("--folds", type=tq.parse_folds, default=(1, 2, 3, 4, 5))
    parser.add_argument("--max-subjects", type=int, default=None)
    parser.add_argument("--bootstrap-replicates", type=int, default=DEFAULT_BOOTSTRAPS)
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--skip-plots", action="store_true")
    parser.add_argument(
        "--validation-only",
        action="store_true",
        help="Stop after fold-wise validation without loading outer-test data.",
    )
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    if args.max_subjects is not None and args.max_subjects < 2:
        parser.error("--max-subjects must be at least 2")
    if args.bootstrap_replicates < 100:
        parser.error("--bootstrap-replicates must be at least 100")
    return args


if __name__ == "__main__":
    destination = run(parse_args())
    print(f"\nSaved Adaptive Quantile Profile run: {destination.resolve()}")
