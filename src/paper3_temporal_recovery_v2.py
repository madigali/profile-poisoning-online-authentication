#!/usr/bin/env python3
"""TQ-EMA v2: recovery-episode balancing under clean claimant drift.

Version 2 retains the complete TQ-EMA v1 authentication, quarantine, robust
target, movement-cap, and enrollment-anchor rules.  Its sole new principle is
a finite RECOVERY_DOWN state.  After a confirmed downward batch, trusted EMA
proposals that would raise either the production mean or the derived threshold
are temporarily suppressed.  Authentication decisions never change.

Fold-specific parameters are selected from validation scores only.  The outer
test protocol is locked to claimant-only D={0,1,2}; because those outer caches
were already inspected for v1, v2 results are exploratory rather than a fresh
confirmatory holdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import shlex
import sys
from dataclasses import asdict
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
import paper3_temporal_recovery as v1


EPISODE_HORIZON = 3
VALIDATION_FAR_LIMIT = 0.01
VALIDATION_HTER_LIMIT = 0.005
DEFAULT_DRIFTS = (0.0, 1.0, 2.0)
DEFAULT_BOOTSTRAPS = 10_000
RATE_COLUMNS = set(v1.RATE_COLUMNS) | {
    "episode_active_rate",
    "episode_entry_rate",
    "conflicting_trusted_suppression_rate",
    "episode_trusted_candidate_rate",
    "episode_allowed_trusted_update_rate",
}


class ValidationSelectionFailure(RuntimeError):
    """Raised after diagnostics are saved when any fold has no feasible v2."""


def preview_moment_update(agent: object, target: float, alpha: float,
                          min_sigma: float = 1e-4) -> tuple[float, float]:
    mean = (1.0 - alpha) * float(agent.mean) + alpha * float(target)
    second = (
        (1.0 - alpha) * float(agent.second_moment)
        + alpha * float(target) ** 2
    )
    threshold = v1.derived_threshold(mean, second, float(agent.k), min_sigma)
    return mean, threshold


class RecoveryEpisodeEMA(v1.TemporalQuarantineEMA):
    """TQ-EMA with a fixed-horizon downward-recovery controller state."""

    def __init__(self, *args, episode_horizon: int = EPISODE_HORIZON, **kwargs):
        super().__init__(*args, **kwargs)
        if episode_horizon < 1:
            raise ValueError("episode_horizon must be positive")
        self.episode_horizon = int(episode_horizon)
        self.episode_remaining = 0
        self.episode_entries = 0
        self.episode_refreshes = 0
        self.episode_exits = 0
        self.episode_active_observations = 0
        self.episode_trusted_candidates = 0
        self.suppressed_conflicting_trusted_updates = 0
        self.episode_allowed_trusted_updates = 0

    @property
    def in_recovery_episode(self) -> bool:
        return self.episode_remaining > 0

    def _enter_or_refresh_episode(self) -> None:
        if self.in_recovery_episode:
            self.episode_refreshes += 1
        else:
            self.episode_entries += 1
        self.episode_remaining = self.episode_horizon

    def _advance_episode(self) -> None:
        if not self.in_recovery_episode:
            return
        self.episode_remaining -= 1
        if self.episode_remaining == 0:
            self.episode_exits += 1

    def process(self, score: float, session_id: int) -> dict[str, float | int | str]:
        score = float(score)
        session_id = int(session_id)
        episode_before = self.in_recovery_episode
        threshold_before = self.threshold
        update_threshold_before = self.update_threshold
        mean_before = float(self.agent.mean)
        authenticated = score >= threshold_before
        event = ""
        updated = False
        suppressed = False
        episode_refreshed = False
        transition_scale = 0.0
        target = float("nan")

        if authenticated:
            self.reset_quarantine()
            if score >= update_threshold_before:
                proposed_mean, proposed_threshold = preview_moment_update(
                    self.agent, score, float(self.agent.alpha), self.min_sigma
                )
                conflicting = (
                    proposed_mean > mean_before + 1e-12
                    or proposed_threshold > threshold_before + 1e-12
                )
                if episode_before:
                    self.episode_trusted_candidates += 1
                if episode_before and conflicting:
                    event = "trusted_upward_suppressed"
                    suppressed = True
                    self.suppressed_conflicting_trusted_updates += 1
                else:
                    event = (
                        "episode_nonincreasing_trusted_update"
                        if episode_before else "trusted_update"
                    )
                    transition = self._transition(
                        score, float(self.agent.alpha), recovery=False
                    )
                    updated = transition.applied
                    transition_scale = transition.scale
                    if updated:
                        self.trusted_updates += 1
                        if episode_before:
                            self.episode_allowed_trusted_updates += 1
                    else:
                        self.rejected_transitions += 1
            else:
                event = "ordinary_accept"
        elif score >= threshold_before - self.config.band_sigma * self.sigma_enroll:
            event = "recovery_candidate"
            self.recovery_candidates += 1
            if not self.quarantine_scores:
                self.quarantine_reference_mean = mean_before
            if session_id in self.quarantine_sessions:
                raise AssertionError("Recovery evidence must come from distinct sessions")
            if self.quarantine_reference_mean is None:
                raise AssertionError("Missing quarantine reference mean")
            if not score < self.quarantine_reference_mean:
                self.reset_quarantine()
                event = "recovery_direction_reset"
            else:
                self.quarantine_scores.append(score)
                self.quarantine_sessions.append(session_id)
                if len(self.quarantine_scores) == self.config.confirmation_sessions:
                    batch = np.asarray(self.quarantine_scores, dtype=float)
                    if float(np.ptp(batch)) > (
                        self.config.dispersion_sigma * self.sigma_enroll + 1e-12
                    ):
                        event = "recovery_dispersion_reset"
                    else:
                        self.recovery_confirmations += 1
                        target = float(np.median(batch))
                        transition = self._transition(
                            target, self.config.recovery_alpha, recovery=True
                        )
                        updated = transition.applied
                        transition_scale = transition.scale
                        event = (
                            "recovery_update_episode_enter"
                            if updated else "recovery_episode_enter_transition_rejected"
                        )
                        if updated:
                            self.recovery_updates += 1
                        else:
                            self.rejected_transitions += 1
                        self._enter_or_refresh_episode()
                        episode_refreshed = True
                    self.reset_quarantine()
        else:
            event = "clear_reject"
            self.reset_quarantine()

        if episode_before or episode_refreshed:
            self.episode_active_observations += 1
        if episode_before and not episode_refreshed:
            self._advance_episode()

        return {
            "event": event,
            "authenticated": int(authenticated),
            "updated": int(updated),
            "suppressed": int(suppressed),
            "threshold_before": threshold_before,
            "update_threshold_before": update_threshold_before,
            "threshold_after": self.threshold,
            "mean_before": mean_before,
            "mean_after": float(self.agent.mean),
            "transition_scale": transition_scale,
            "recovery_target": target,
            "quarantine_size_after": len(self.quarantine_scores),
            "episode_before": int(episode_before),
            "episode_after": int(self.in_recovery_episode),
            "episode_remaining_after": self.episode_remaining,
        }


def evaluate_v2_pairs(
    config: v1.TQConfig,
    sid: int,
    tau0: float,
    enrollment: np.ndarray,
    pairs: Sequence[tuple[int, int, int]],
    genuine_scores: np.ndarray,
    impostor_score_matrix: np.ndarray,
    y: np.ndarray,
    session: np.ndarray,
    within: np.ndarray,
    core,
    attack_v2,
) -> tuple[dict, list[dict], list[dict]]:
    agent = core.AdaptiveEMA.from_enrollment(enrollment, float(tau0))
    before = attack_v2.profile_snapshot(agent)
    min_sigma = float(getattr(core, "AGENT_MIN_SIGMA", 1e-4))
    controller = RecoveryEpisodeEMA(
        agent, enrollment, float(tau0), config, min_sigma,
        episode_horizon=EPISODE_HORIZON,
    )
    checkpoint_rows: list[dict] = []
    source_rows: list[dict] = []
    rejections: list[bool] = []
    fars: list[float] = []
    adaptation_accepts = 0

    for checkpoint, (session_id, adaptation_index, probe_index) in enumerate(pairs):
        adaptation_score = float(genuine_scores[adaptation_index, sid])
        event = controller.process(adaptation_score, session_id)
        adaptation_accepts += int(event["authenticated"])
        profile = attack_v2.profile_snapshot(agent)
        probe_score = float(genuine_scores[probe_index, sid])
        accepted = probe_score >= profile.threshold
        rejections.append(not accepted)
        far, source_values = v1.source_macro_far(
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
        checkpoint_rows.append({
            "checkpoint": checkpoint, "session": session_id,
            "adaptation_index": adaptation_index, "probe_index": probe_index,
            "adaptation_score": adaptation_score, "probe_score": probe_score,
            "auth_threshold_before": event["threshold_before"],
            "update_threshold_before": event["update_threshold_before"],
            "threshold": profile.threshold, "mean": profile.mean, "sigma": profile.sigma,
            "adaptation_authenticated": event["authenticated"],
            "updated": event["updated"], "suppressed": event["suppressed"],
            "accepted": int(accepted), "checkpoint_FAR": far,
            "n_impostor_sources": len(source_values),
            "updates_so_far": controller.trusted_updates + controller.recovery_updates,
            "event": event["event"], "transition_scale": event["transition_scale"],
            "recovery_target": event["recovery_target"],
            "quarantine_size_after": event["quarantine_size_after"],
            "episode_before": event["episode_before"],
            "episode_after": event["episode_after"],
            "episode_remaining_after": event["episode_remaining_after"],
        })

    after = attack_v2.profile_snapshot(agent)
    early_reject, late_reject = v1.endpoint_split(rejections)
    early_far, late_far = v1.endpoint_split(fars)
    attempts = len(pairs)
    updates = controller.trusted_updates + controller.recovery_updates
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
        "adaptation_attempts": attempts,
        "adaptation_accepts": adaptation_accepts,
        "adaptation_auth_rate": adaptation_accepts / attempts,
        "genuine_updates": updates,
        "GUR": updates / attempts,
        "trusted_updates": controller.trusted_updates,
        "recovery_updates": controller.recovery_updates,
        "trusted_update_rate": controller.trusted_updates / attempts,
        "recovery_update_rate": controller.recovery_updates / attempts,
        "recovery_candidates": controller.recovery_candidates,
        "recovery_candidate_rate": controller.recovery_candidates / attempts,
        "recovery_confirmations": controller.recovery_confirmations,
        "recovery_confirmation_rate": controller.recovery_confirmations / attempts,
        "quarantine_resets": controller.quarantine_resets,
        "rejected_transitions": controller.rejected_transitions,
        "episode_entries": controller.episode_entries,
        "episode_entry_rate": controller.episode_entries / attempts,
        "episode_refreshes": controller.episode_refreshes,
        "episode_exits": controller.episode_exits,
        "episode_active_observations": controller.episode_active_observations,
        "episode_active_rate": controller.episode_active_observations / attempts,
        "episode_trusted_candidates": controller.episode_trusted_candidates,
        "episode_trusted_candidate_rate": controller.episode_trusted_candidates / attempts,
        "suppressed_conflicting_trusted_updates": (
            controller.suppressed_conflicting_trusted_updates
        ),
        "conflicting_trusted_suppression_rate": (
            controller.suppressed_conflicting_trusted_updates / attempts
        ),
        "episode_allowed_trusted_updates": controller.episode_allowed_trusted_updates,
        "episode_allowed_trusted_update_rate": (
            controller.episode_allowed_trusted_updates / attempts
        ),
        "n_checkpoint_probes": attempts,
        "n_early_probes": len(early_reject), "n_late_probes": len(late_reject),
        "n_checkpoint_sessions": attempts, "non_stricter_gate_states": 0,
        "mu_enroll": controller.mu_enroll, "sigma_enroll": controller.sigma_enroll,
        **guard.profile_fields(before, after),
    }
    return metrics, checkpoint_rows, source_rows


def select_validation_config(candidate_summary: pd.DataFrame) -> pd.Series:
    frame = candidate_summary.copy()
    frame["feasible"] = (
        (frame["late_FAR_change"] <= VALIDATION_FAR_LIMIT + 1e-12)
        & (frame["HTER_change"] <= VALIDATION_HTER_LIMIT + 1e-12)
    )
    feasible = frame[frame["feasible"]]
    if not len(feasible):
        raise RuntimeError(
            "No v2 configuration satisfies validation Delta-FAR <= +1pp and "
            "HTER degradation <= +0.5pp"
        )
    ordered = feasible.sort_values(
        [
            "late_FRR_gain", "conflicting_trusted_suppression_rate",
            "recovery_update_rate", "confirmation_sessions", "band_sigma",
            "recovery_alpha", "anchor_sigma", "config_id",
        ],
        ascending=[False, False, False, False, True, True, True, True],
        kind="mergesort",
    )
    selected = ordered.iloc[0].copy()
    selected["selection_status"] = "feasible"
    return selected


def tune_fold(fold: int, cache_dir: Path, core, attack_v2,
              max_subjects: int | None) -> tuple[v1.TQConfig | None, pd.DataFrame, pd.DataFrame, dict]:
    payload = v1.load_validation_payload(cache_dir, fold)
    drift_scores, drift_seed = v1.load_validation_drift_scores(
        core, cache_dir, fold, v1.VALIDATION_DRIFT
    )
    clean_scores = payload["val_scores"].astype(np.float64)
    y, session, within = (
        payload["y_val"], payload["session_val"], payload["within_val"]
    )
    rows: list[dict] = []
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
        if len(enrollment) < 2 or not len(validation_impostor):
            exclusions.append({
                "fold": fold, "sid": sid,
                "reason": "insufficient validation enrollment/calibration",
            })
            continue
        _, tau0 = core.eer_from_scores(enrollment, validation_impostor)
        frozen = v1.frozen_pair_metrics(
            sid, float(tau0), pairs, drift_scores, clean_scores,
            y, session, within,
        )
        for config in v1.tq_grid():
            metrics, _, _ = evaluate_v2_pairs(
                config, sid, float(tau0), enrollment, pairs, drift_scores,
                clean_scores, y, session, within, core, attack_v2,
            )
            rows.append({
                "fold": fold, "sid": sid, "config_id": config.config_id,
                **asdict(config),
                "late_FRR": metrics["late_FRR"],
                "late_FAR": metrics["late_FAR"], "HTER": metrics["HTER"],
                "frozen_late_FRR": frozen["late_FRR"],
                "frozen_late_FAR": frozen["late_FAR"],
                "frozen_HTER": frozen["HTER"],
                "late_FRR_gain": frozen["late_FRR"] - metrics["late_FRR"],
                "late_FAR_change": metrics["late_FAR"] - frozen["late_FAR"],
                "HTER_change": metrics["HTER"] - frozen["HTER"],
                "GUR": metrics["GUR"],
                "recovery_update_rate": metrics["recovery_update_rate"],
                "episode_entry_rate": metrics["episode_entry_rate"],
                "episode_active_rate": metrics["episode_active_rate"],
                "conflicting_trusted_suppression_rate": (
                    metrics["conflicting_trusted_suppression_rate"]
                ),
            })

    subject_frame = pd.DataFrame(rows)
    if subject_frame.empty:
        raise RuntimeError(f"Fold {fold}: no eligible validation subjects")
    keys = ["config_id"] + list(asdict(v1.tq_grid()[0]).keys())
    metrics = [
        "late_FRR", "late_FAR", "HTER", "frozen_late_FRR",
        "frozen_late_FAR", "frozen_HTER", "late_FRR_gain",
        "late_FAR_change", "HTER_change", "GUR", "recovery_update_rate",
        "episode_entry_rate", "episode_active_rate",
        "conflicting_trusted_suppression_rate",
    ]
    summary = subject_frame.groupby(keys, as_index=False)[metrics].mean()
    counts = subject_frame.groupby(keys, as_index=False).agg(n_subjects=("sid", "nunique"))
    summary = summary.merge(counts, on=keys)
    summary.insert(0, "fold", fold)
    try:
        selected = select_validation_config(summary)
    except RuntimeError:
        diagnostic = summary.sort_values(
            [
                "late_FRR_gain", "conflicting_trusted_suppression_rate",
                "recovery_update_rate", "config_id",
            ],
            ascending=[False, False, False, True],
            kind="mergesort",
        ).iloc[0]
        metadata = {
            "fold": fold, "validation_drift": v1.VALIDATION_DRIFT,
            "validation_drift_seed": drift_seed,
            "selection_status": "no_feasible_config",
            "selected_config_id": "",
            "best_unconstrained_config_id": str(diagnostic["config_id"]),
            "best_unconstrained_late_FRR_gain": float(diagnostic["late_FRR_gain"]),
            "best_unconstrained_late_FAR_change": float(diagnostic["late_FAR_change"]),
            "best_unconstrained_HTER_change": float(diagnostic["HTER_change"]),
            "minimum_validation_late_FAR_change": float(summary["late_FAR_change"].min()),
            "minimum_validation_HTER_change": float(summary["HTER_change"].min()),
            "n_feasible_configs": 0,
            "n_validation_subjects": int(diagnostic["n_subjects"]),
            "n_validation_exclusions": len(exclusions),
        }
        return None, subject_frame, summary, {
            "metadata": metadata, "exclusions": exclusions
        }
    config = v1.TQConfig(
        band_sigma=float(selected["band_sigma"]),
        confirmation_sessions=int(selected["confirmation_sessions"]),
        recovery_alpha=float(selected["recovery_alpha"]),
        anchor_sigma=float(selected["anchor_sigma"]),
    )
    metadata = {
        "fold": fold, "validation_drift": v1.VALIDATION_DRIFT,
        "validation_drift_seed": drift_seed,
        "selection_status": str(selected["selection_status"]),
        "selected_config_id": config.config_id,
        "selected_validation_late_FRR_gain": float(selected["late_FRR_gain"]),
        "selected_validation_late_FAR_change": float(selected["late_FAR_change"]),
        "selected_validation_HTER_change": float(selected["HTER_change"]),
        "selected_validation_suppression_rate": float(
            selected["conflicting_trusted_suppression_rate"]
        ),
        "n_feasible_configs": int((
            (summary["late_FAR_change"] <= VALIDATION_FAR_LIMIT + 1e-12)
            & (summary["HTER_change"] <= VALIDATION_HTER_LIMIT + 1e-12)
        ).sum()),
        "n_validation_subjects": int(selected["n_subjects"]),
        "n_validation_exclusions": len(exclusions),
    }
    return config, subject_frame, summary, {"metadata": metadata, "exclusions": exclusions}


def load_v1_selections(path: Path, folds: Sequence[int]) -> dict[int, v1.TQConfig]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing frozen v1 selection table: {path}")
    frame = pd.read_csv(path)
    configs: dict[int, v1.TQConfig] = {}
    for fold in folds:
        row = frame[frame["fold"] == fold]
        if len(row) != 1:
            raise ValueError(f"Expected one frozen v1 selection for fold {fold}")
        item = row.iloc[0]
        configs[fold] = v1.TQConfig(
            band_sigma=float(item["band_sigma"]),
            confirmation_sessions=int(item["confirmation_sessions"]),
            recovery_alpha=float(item["recovery_alpha"]),
            anchor_sigma=float(item["anchor_sigma"]),
        )
    return configs


def percentage_export(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    selected_rates = {
        "selected_validation_late_FRR_gain",
        "selected_validation_late_FAR_change",
        "selected_validation_HTER_change",
        "selected_validation_suppression_rate",
        "best_unconstrained_late_FRR_gain",
        "best_unconstrained_late_FAR_change",
        "best_unconstrained_HTER_change",
        "minimum_validation_late_FAR_change",
        "minimum_validation_HTER_change",
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


def save_trajectory_plots(checkpoints: pd.DataFrame, output_dir: Path) -> None:
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    methods = [
        "Frozen", "Blind EMA", "Guarded EMA", "Oracle-all-genuine",
        "TQ-EMA v1", "TQ-EMA v2",
    ]
    colors = {
        "Frozen": "#4b5563", "Blind EMA": "#d97706", "Guarded EMA": "#2563eb",
        "Oracle-all-genuine": "#059669", "TQ-EMA v1": "#be123c",
        "TQ-EMA v2": "#7c3aed",
    }
    frame = checkpoints.copy()
    frame["path_length"] = frame.groupby(
        ["fold", "D", "sid", "policy_id"]
    )["checkpoint"].transform("size")
    frame = frame[frame["path_length"] == 5]
    for drift_value, group in frame.groupby("D", sort=True):
        n_paths = group[["fold", "sid"]].drop_duplicates().shape[0]
        aggregate = group.groupby(["method", "checkpoint"], as_index=False).agg(
            adaptation_score=("adaptation_score", "mean"),
            probe_score=("probe_score", "mean"), threshold=("threshold", "mean"),
            mean=("mean", "mean"), sigma=("sigma", "mean"),
            auth_rate=("adaptation_authenticated", "mean"),
            update_rate=("updated", "mean"),
            suppression_rate=("suppressed", "mean"),
        )
        score_path = group.groupby("checkpoint", as_index=False).agg(
            adaptation_score=("adaptation_score", "mean"),
            probe_score=("probe_score", "mean"),
        )
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
        for method in methods:
            values = aggregate[aggregate["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, values["mean"], marker="o",
                        color=colors[method], label=method)
        ax.set(title="EMA profile mean", xlabel="Session checkpoint", ylabel="Mean score")
        ax.legend(fontsize=7.5)

        ax = axes[1, 0]
        for method in methods:
            values = aggregate[aggregate["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, values["sigma"], marker="o",
                        color=colors[method], label=method)
        ax.set(title="EMA profile sigma", xlabel="Session checkpoint", ylabel="Sigma")
        ax.legend(fontsize=7.5)

        ax = axes[1, 1]
        for method in methods:
            values = aggregate[aggregate["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, 100 * values["update_rate"],
                        color=colors[method], marker="o", linewidth=2,
                        label=f"{method} update")
        v2_values = aggregate[aggregate["method"] == "TQ-EMA v2"]
        if len(v2_values):
            ax.plot(v2_values["checkpoint"] + 1, 100 * v2_values["suppression_rate"],
                    color=colors["TQ-EMA v2"], marker="x", linestyle="--",
                    linewidth=1.8, label="TQ-EMA v2 suppression")
        ax.set(title="Production updates and v2 suppression",
               xlabel="Session checkpoint", ylabel="Rate (%)", ylim=(-2, 102))
        ax.legend(fontsize=7.2)
        for axis in axes.flat:
            axis.grid(alpha=0.25)
        fig.suptitle(
            f"Claimant-only clean drift, D={drift_value:g} "
            f"({n_paths} complete subject-fold paths)", fontsize=14,
        )
        fig.savefig(
            figure_dir / f"tq_v2_trajectory_claimant_only_D{drift_value:.1f}.png",
            dpi=180,
        )
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
    return Path("results") / f"{datetime.now():%Y%m%d-%H%M%S}-tq-v2-clean-drift"


def run(args: argparse.Namespace) -> Path:
    source_dir = Path(args.source_dir).resolve()
    cache_dir = Path(args.cache_dir).resolve() if args.cache_dir else source_dir / "paper3_cache"
    output_dir = resolve_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    core, attack_v2 = guard.load_canonical_modules(source_dir)
    folds = tuple(args.folds)
    v1_selection_path = (
        Path(args.v1_selection_csv).resolve()
        if args.v1_selection_csv
        else source_dir / "results" / "paper3_tq_clean_drift_20261001_v1"
        / "paper3_tq_selected_by_fold.csv"
    )
    frozen_v1_configs = load_v1_selections(v1_selection_path, folds)

    config_payload = {
        "source_dir": str(source_dir), "cache_dir": str(cache_dir),
        "folds": list(folds), "max_subjects": args.max_subjects,
        "drifts": list(args.drifts), "scenario": "claimant_only",
        "method": "TQ-EMA v2 recovery episode",
        "episode_horizon_sessions": EPISODE_HORIZON,
        "conflict_rule": "suppress trusted proposal if proposed mean OR threshold increases",
        "validation_replay": (
            "all clean D=0 validation scores initialize/calibrate; D=2 transformed "
            "validation scores are replayed; impostor checkpoints remain D=0"
        ),
        "validation_far_limit": VALIDATION_FAR_LIMIT,
        "validation_hter_degradation_limit": VALIDATION_HTER_LIMIT,
        "tq_grid": [asdict(config) for config in v1.tq_grid()],
        "v1_selection_csv": str(v1_selection_path),
        "primary_test": "claimant-only D=2, TQ-EMA v2 versus Frozen late-FRR gain",
        "bootstrap_replicates": args.bootstrap_replicates,
        "bootstrap_seed": args.seed,
        "inferential_status": "exploratory reuse of outer caches already inspected for v1",
    }
    (output_dir / "config.json").write_text(
        json.dumps(config_payload, indent=2) + "\n", encoding="utf-8"
    )
    status = "running"
    log: list[str] = []

    try:
        selected_configs: dict[int, v1.TQConfig] = {}
        validation_subject_frames: list[pd.DataFrame] = []
        validation_summary_frames: list[pd.DataFrame] = []
        selection_rows: list[dict] = []
        exclusions: list[dict] = []
        validation_failures: list[dict] = []

        for fold in folds:
            selected, subject_frame, candidate_summary, details = tune_fold(
                fold, cache_dir, core, attack_v2, args.max_subjects
            )
            validation_subject_frames.append(subject_frame)
            validation_summary_frames.append(candidate_summary)
            if selected is None:
                selection_rows.append(details["metadata"])
                validation_failures.append(details["metadata"])
                message = f"Fold {fold}: no feasible v2 validation configuration"
            else:
                selected_configs[fold] = selected
                selection_rows.append({**details["metadata"], **asdict(selected)})
                message = f"Fold {fold}: selected v2 {selected.config_id} on validation only"
            exclusions.extend(
                {"stage": "validation", **row} for row in details["exclusions"]
            )
            print(message, flush=True)
            log.append(message)

        validation_subject = pd.concat(validation_subject_frames, ignore_index=True)
        validation_candidates = pd.concat(validation_summary_frames, ignore_index=True)
        selected_frame = pd.DataFrame(selection_rows)
        percentage_export(validation_subject).to_csv(
            output_dir / "paper3_tq_v2_validation_subject.csv", index=False
        )
        percentage_export(validation_candidates).to_csv(
            output_dir / "paper3_tq_v2_validation_candidates.csv", index=False
        )
        percentage_export(selected_frame).to_csv(
            output_dir / "paper3_tq_v2_selected_by_fold.csv", index=False
        )

        if validation_failures:
            failure_payload = {
                "status": "validation_failed",
                "reason": (
                    "At least one fold had no configuration satisfying validation "
                    "Delta-FAR <= +1pp and HTER degradation <= +0.5pp"
                ),
                "failed_folds": [int(item["fold"]) for item in validation_failures],
                "fold_diagnostics": validation_failures,
                "outer_test_loaded": False,
            }
            (output_dir / "validation_failure.json").write_text(
                json.dumps(failure_payload, indent=2) + "\n", encoding="utf-8"
            )
            pd.DataFrame(exclusions).to_csv(output_dir / "exclusions.csv", index=False)
            status = "validation_failed"
            raise ValidationSelectionFailure(failure_payload["reason"])

        rows: list[dict] = []
        checkpoints: list[dict] = []
        source_far_rows: list[dict] = []
        policies = v1.baseline_policies()

        for fold in folds:
            clean = attack_v2.load_fold(cache_dir, fold, drift=0.0)
            selected_v2 = selected_configs[fold]
            selected_v1 = frozen_v1_configs[fold]
            val_scores, y_val = clean["val_scores"], clean["y_val"]
            y_test = clean["y_test"]
            session_test, within_test = clean["session_test"], clean["within_test"]
            clean_scores = clean["test_scores"]
            for drift_value in args.drifts:
                drifted = attack_v2.load_fold(cache_dir, fold, drift=drift_value)
                for field in ("y_test", "session_test", "within_test"):
                    if not np.array_equal(clean[field], drifted[field]):
                        raise AssertionError(
                            f"Cache alignment failed fold={fold}, D={drift_value}, {field}"
                        )
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
                    except ValueError as exc:
                        exclusions.append({
                            "stage": "test", "fold": fold, "D": drift_value,
                            "sid": sid, "reason": str(exc),
                        })
                        continue
                    _, tau0 = core.eer_from_scores(enrollment, validation_impostor)

                    for policy in policies:
                        metrics, probe_rows = drift.evaluate_subject_policy(
                            policy, sid, float(tau0), enrollment, genuine_idx,
                            drift_scores, clean_scores, y_test, session_test,
                            within_test, core, attack_v2,
                        )
                        identity = {
                            "fold": fold, "scenario": "claimant_only", "D": float(drift_value),
                            "sid": sid, "policy_id": policy.policy_id,
                            "method": policy.method, "lambda": policy.lambda_label,
                            "lambda_value": policy.lambda_value, "tau0": float(tau0),
                            "selected_config_id": selected_v2.config_id,
                        }
                        rows.append({**identity, **metrics})
                        checkpoints.extend({**identity, **probe} for probe in probe_rows)
                        if float(drift_value) == 2.0 and policy.policy_id == "frozen":
                            sources = v1.source_rows_from_checkpoints(
                                probe_rows[-2:], sid, clean_scores, y_test,
                                session_test, within_test,
                            )
                            source_far_rows.extend({**identity, **source} for source in sources)

                    v1_metrics, v1_checkpoints, _ = v1.evaluate_tq_pairs(
                        selected_v1, sid, float(tau0), enrollment, pairs,
                        drift_scores, clean_scores, y_test, session_test,
                        within_test, core, attack_v2,
                    )
                    v1_identity = {
                        "fold": fold, "scenario": "claimant_only", "D": float(drift_value),
                        "sid": sid, "policy_id": "tq_v1", "method": "TQ-EMA v1",
                        "lambda": f"{v1.TRUSTED_LAMBDA:.2f}",
                        "lambda_value": v1.TRUSTED_LAMBDA, "tau0": float(tau0),
                        "selected_config_id": selected_v1.config_id,
                    }
                    rows.append({**v1_identity, **v1_metrics})
                    checkpoints.extend({**v1_identity, **probe} for probe in v1_checkpoints)

                    v2_metrics, v2_checkpoints, v2_sources = evaluate_v2_pairs(
                        selected_v2, sid, float(tau0), enrollment, pairs,
                        drift_scores, clean_scores, y_test, session_test,
                        within_test, core, attack_v2,
                    )
                    v2_identity = {
                        "fold": fold, "scenario": "claimant_only", "D": float(drift_value),
                        "sid": sid, "policy_id": "tq_ema", "method": "TQ-EMA v2",
                        "lambda": f"{v1.TRUSTED_LAMBDA:.2f}",
                        "lambda_value": v1.TRUSTED_LAMBDA, "tau0": float(tau0),
                        "selected_config_id": selected_v2.config_id,
                    }
                    rows.append({**v2_identity, **v2_metrics})
                    checkpoints.extend({**v2_identity, **probe} for probe in v2_checkpoints)
                    if float(drift_value) == 2.0:
                        first_late = len(pairs) - 2
                        source_far_rows.extend(
                            {**v2_identity, **source}
                            for source in v2_sources
                            if int(source["checkpoint"]) >= first_late
                        )

            message = f"Fold {fold}: locked outer test complete"
            print(message, flush=True)
            log.append(message)

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
        source_frame = pd.DataFrame(source_far_rows)
        two_way = v1.two_way_far_bootstrap(
            source_frame, args.bootstrap_replicates, args.seed + 911
        )
        assessment = v1.primary_assessment(summary, bootstrap)
        assessment["primary_comparison"] = "TQ-EMA v2 versus Frozen"
        assessment["inferential_status"] = (
            "exploratory reuse of outer score caches already inspected for v1"
        )

        percentage_export(subject_fold).to_csv(
            output_dir / "paper3_tq_v2_subject_fold.csv", index=False
        )
        percentage_export(by_fold).to_csv(
            output_dir / "paper3_tq_v2_by_fold_descriptive.csv", index=False
        )
        percentage_export(by_subject).to_csv(
            output_dir / "paper3_tq_v2_by_subject.csv", index=False
        )
        percentage_export(summary).to_csv(
            output_dir / "paper3_tq_v2_summary.csv", index=False
        )
        checkpoint_frame = pd.DataFrame(checkpoints)
        if "suppressed" not in checkpoint_frame:
            checkpoint_frame["suppressed"] = 0
        checkpoint_frame["suppressed"] = checkpoint_frame["suppressed"].fillna(0)
        percentage_export(checkpoint_frame).to_csv(
            output_dir / "paper3_tq_v2_checkpoints.csv", index=False
        )
        percentage_export(source_frame).to_csv(
            output_dir / "paper3_tq_v2_source_far.csv.gz", index=False,
            compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
        )
        bootstrap_export = bootstrap.copy()
        bootstrap_export[["estimate", "ci95_low", "ci95_high"]] *= 100.0
        bootstrap_export.to_csv(
            output_dir / "paper3_tq_v2_paired_subject_bootstrap.csv", index=False
        )
        if len(two_way):
            two_way_export = two_way.copy()
            two_way_export[["estimate", "ci95_low", "ci95_high"]] *= 100.0
            two_way_export.to_csv(
                output_dir / "paper3_tq_v2_two_way_far_bootstrap.csv", index=False
            )
        assessment_export = assessment.copy()
        for key in [
            "late_FRR_gain", "late_FRR_gain_ci95_low", "late_FRR_gain_ci95_high",
            "late_FAR_change", "HTER_change", "complete_case_late_FRR_gain_ci95_low",
        ]:
            assessment_export[key] = 100.0 * float(assessment_export[key])
        (output_dir / "primary_assessment.json").write_text(
            json.dumps(assessment_export, indent=2) + "\n", encoding="utf-8"
        )
        pd.DataFrame(exclusions).to_csv(output_dir / "exclusions.csv", index=False)
        if not args.skip_plots:
            save_trajectory_plots(checkpoint_frame, output_dir)

        display = percentage_export(summary)[[
            "D", "method", "late_FRR", "late_FAR", "HTER", "GUR",
            "threshold_delta", "adaptation_gain",
        ]]
        print("\nTQ-EMA v2 clean-drift summary (subject macro means):")
        print(display.round(5).to_string(index=False))
        print("\nPrimary assessment:")
        print(json.dumps(assessment_export, indent=2))
        log.extend(["", display.round(5).to_string(index=False), "", json.dumps(assessment_export, indent=2)])
        status = "complete"
        return output_dir
    finally:
        (output_dir / "run.log").write_text("\n".join(log) + "\n", encoding="utf-8")
        source_paths = {
            "hmog_revised_experiment.py": Path(core.__file__).resolve(),
            "paper3_poisoning_attack_v2.py": Path(attack_v2.__file__).resolve(),
            "paper3_guarded_adaptation.py": Path(guard.__file__).resolve(),
            "paper3_guarded_drift.py": Path(drift.__file__).resolve(),
            "paper3_temporal_recovery.py": Path(v1.__file__).resolve(),
            "paper3_temporal_recovery_v2.py": Path(__file__).resolve(),
            "v1_selection_csv": v1_selection_path,
        }
        cache_hashes = {}
        for fold in folds:
            for suffix in ["base.npz", "model.pt"] + [f"D{value:.1f}.npz" for value in args.drifts]:
                path = cache_dir / f"fold{fold}_{suffix}"
                if path.is_file():
                    cache_hashes[path.name] = sha256(path)
        manifest = {
            "status": status, "created_utc": datetime.now(timezone.utc).isoformat(),
            "command": shlex.join(sys.argv), "python": sys.version,
            "platform": platform.platform(),
            "source_hashes": {
                name: sha256(path) for name, path in source_paths.items() if path.is_file()
            },
            "cache_hashes": cache_hashes,
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=".")
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--v1-selection-csv", default=None)
    parser.add_argument("--drifts", type=drift.parse_drifts, default=DEFAULT_DRIFTS)
    parser.add_argument("--folds", type=v1.parse_folds, default=(1, 2, 3, 4, 5))
    parser.add_argument("--max-subjects", type=int, default=None)
    parser.add_argument("--bootstrap-replicates", type=int, default=DEFAULT_BOOTSTRAPS)
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--skip-plots", action="store_true")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    if args.max_subjects is not None and args.max_subjects < 2:
        parser.error("--max-subjects must be at least 2")
    if args.bootstrap_replicates < 100:
        parser.error("--bootstrap-replicates must be at least 100")
    return args


if __name__ == "__main__":
    destination = run(parse_args())
    print(f"\nSaved TQ-EMA v2 clean-drift run: {destination.resolve()}")
