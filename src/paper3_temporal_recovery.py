#!/usr/bin/env python3
"""Validation-selected Temporal Quarantine EMA clean-drift experiment.

TQ-EMA separates authentication from adaptation evidence.  A rejected score
never grants access and never updates the production profile directly.  A
borderline rejected score may enter an isolated quarantine; only a temporally
consistent batch from distinct consecutive sessions can propose a bounded EMA
moment update.

The deliberately small hyperparameter grid is selected independently inside
each outer fold using only that fold's validation partition.  The first two
validation session pairs initialize the inner profile and the remaining pairs
form a claimant-only D=2 tuning stream.  Test scores are not loaded until the
fold's configuration has been selected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import shlex
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import paper3_guarded_adaptation as guard
import paper3_guarded_drift as drift


DEFAULT_DRIFTS = (0.0, 1.0, 2.0)
DEFAULT_BOOTSTRAPS = 10_000
VALIDATION_DRIFT = 2.0
TRUSTED_LAMBDA = 0.25
BAND_SIGMAS = (0.25, 0.50, 0.75)
CONFIRMATION_SESSIONS = (2, 3)
RECOVERY_ALPHAS = (0.025, 0.050)
ANCHOR_SIGMAS = (0.10, 0.25)
DISPERSION_SIGMA = 0.50
MEAN_CAP_SIGMA = 0.10
THRESHOLD_CAP_SIGMA = 0.05
VALIDATION_FAR_LIMIT = 0.01
TEST_HTER_LIMIT = 0.005
RATE_COLUMNS = set(drift.RATE_COLUMNS) | {
    "recovery_candidate_rate",
    "recovery_confirmation_rate",
    "trusted_update_rate",
    "recovery_update_rate",
    "source_FAR",
    "late_FRR_gain",
    "late_FAR_change",
    "HTER_change",
    "frozen_late_FAR",
}


@dataclass(frozen=True)
class TQConfig:
    band_sigma: float
    confirmation_sessions: int
    recovery_alpha: float
    anchor_sigma: float
    dispersion_sigma: float = DISPERSION_SIGMA
    mean_cap_sigma: float = MEAN_CAP_SIGMA
    threshold_cap_sigma: float = THRESHOLD_CAP_SIGMA
    trusted_lambda: float = TRUSTED_LAMBDA

    @property
    def config_id(self) -> str:
        return (
            f"b{self.band_sigma:.2f}_m{self.confirmation_sessions}_"
            f"a{self.recovery_alpha:.3f}_A{self.anchor_sigma:.2f}"
        )


@dataclass(frozen=True)
class Transition:
    applied: bool
    scale: float
    mean_before: float
    mean_after: float
    threshold_before: float
    threshold_after: float
    reason: str


def tq_grid() -> list[TQConfig]:
    return [
        TQConfig(band, sessions, alpha, anchor)
        for band in BAND_SIGMAS
        for sessions in CONFIRMATION_SESSIONS
        for alpha in RECOVERY_ALPHAS
        for anchor in ANCHOR_SIGMAS
    ]


def profile_sigma(agent: object, min_sigma: float = 1e-4) -> float:
    variance = float(agent.second_moment) - float(agent.mean) ** 2
    return math.sqrt(max(variance, min_sigma ** 2))


def derived_threshold(mean: float, second_moment: float, k: float,
                      min_sigma: float = 1e-4) -> float:
    sigma = math.sqrt(max(float(second_moment) - float(mean) ** 2, min_sigma ** 2))
    return max(0.0, float(mean) - float(k) * sigma)


def apply_bounded_moment_update(
    agent: object,
    target: float,
    alpha: float,
    mean_cap: float,
    threshold_cap: float,
    threshold_floor: float,
    *,
    require_downward: bool,
    min_sigma: float = 1e-4,
) -> Transition:
    """Move mean and second moment together; never edit threshold directly."""
    old_mean = float(agent.mean)
    old_second = float(agent.second_moment)
    old_threshold = derived_threshold(old_mean, old_second, float(agent.k), min_sigma)
    proposed_mean = (1.0 - alpha) * old_mean + alpha * float(target)
    proposed_second = (1.0 - alpha) * old_second + alpha * float(target) ** 2
    mean_movement = proposed_mean - old_mean
    max_scale = 1.0
    if abs(mean_movement) > mean_cap:
        max_scale = mean_cap / abs(mean_movement)

    # Backtracking is deliberately conservative.  Every candidate state is a
    # convex interpolation of two internally valid moment states.
    for exponent in range(0, 61):
        scale = max_scale * (0.5 ** exponent)
        if scale < 1e-12:
            break
        new_mean = old_mean + scale * (proposed_mean - old_mean)
        new_second = old_second + scale * (proposed_second - old_second)
        new_threshold = derived_threshold(new_mean, new_second, float(agent.k), min_sigma)
        if abs(new_mean - old_mean) > mean_cap + 1e-12:
            continue
        if abs(new_threshold - old_threshold) > threshold_cap + 1e-12:
            continue
        if new_threshold < threshold_floor - 1e-12:
            continue
        if require_downward and not new_threshold < old_threshold - 1e-12:
            continue
        agent.mean = new_mean
        agent.second_moment = new_second
        return Transition(
            True, scale, old_mean, new_mean, old_threshold, new_threshold, "applied"
        )

    reason = "no_safe_downward_transition" if require_downward else "no_safe_transition"
    return Transition(False, 0.0, old_mean, old_mean, old_threshold, old_threshold, reason)


class TemporalQuarantineEMA:
    """Production EMA plus a fully isolated downward-recovery quarantine."""

    def __init__(self, agent: object, enrollment: np.ndarray, tau_enroll: float,
                 config: TQConfig, min_sigma: float = 1e-4):
        self.agent = agent
        self.config = config
        self.mu_enroll = float(np.mean(enrollment))
        self.sigma_enroll = max(float(np.std(enrollment, ddof=0)), min_sigma)
        self.tau_enroll = float(tau_enroll)
        self.min_sigma = float(min_sigma)
        self.quarantine_scores: list[float] = []
        self.quarantine_sessions: list[int] = []
        self.quarantine_reference_mean: float | None = None
        self.quarantine_resets = 0
        self.recovery_candidates = 0
        self.recovery_confirmations = 0
        self.trusted_updates = 0
        self.recovery_updates = 0
        self.rejected_transitions = 0

    @property
    def threshold(self) -> float:
        return float(self.agent.threshold)

    @property
    def update_threshold(self) -> float:
        proposed = self.threshold + self.config.trusted_lambda * (
            self.mu_enroll - self.threshold
        )
        return max(self.threshold, float(proposed))

    def reset_quarantine(self) -> bool:
        had_evidence = bool(self.quarantine_scores)
        if had_evidence:
            self.quarantine_resets += 1
        self.quarantine_scores = []
        self.quarantine_sessions = []
        self.quarantine_reference_mean = None
        return had_evidence

    def _transition(self, target: float, alpha: float, *, recovery: bool) -> Transition:
        return apply_bounded_moment_update(
            self.agent,
            target=float(target),
            alpha=float(alpha),
            mean_cap=self.config.mean_cap_sigma * self.sigma_enroll,
            threshold_cap=self.config.threshold_cap_sigma * self.sigma_enroll,
            threshold_floor=max(
                0.0,
                self.tau_enroll - self.config.anchor_sigma * self.sigma_enroll,
            ),
            require_downward=recovery,
            min_sigma=self.min_sigma,
        )

    def process(self, score: float, session_id: int) -> dict[str, float | int | str]:
        score = float(score)
        session_id = int(session_id)
        threshold_before = self.threshold
        update_threshold_before = self.update_threshold
        mean_before = float(self.agent.mean)
        authenticated = score >= threshold_before
        event = ""
        updated = False
        transition_scale = 0.0
        target = float("nan")

        if authenticated:
            self.reset_quarantine()
            if score >= update_threshold_before:
                event = "trusted_update"
                transition = self._transition(score, float(self.agent.alpha), recovery=False)
                updated = transition.applied
                transition_scale = transition.scale
                if updated:
                    self.trusted_updates += 1
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
                        event = "recovery_update" if updated else "recovery_transition_rejected"
                        if updated:
                            self.recovery_updates += 1
                        else:
                            self.rejected_transitions += 1
                    self.reset_quarantine()
        else:
            event = "clear_reject"
            self.reset_quarantine()

        threshold_after = self.threshold
        return {
            "event": event,
            "authenticated": int(authenticated),
            "updated": int(updated),
            "threshold_before": threshold_before,
            "update_threshold_before": update_threshold_before,
            "threshold_after": threshold_after,
            "mean_before": mean_before,
            "mean_after": float(self.agent.mean),
            "transition_scale": transition_scale,
            "recovery_target": target,
            "quarantine_size_after": len(self.quarantine_scores),
        }


def source_macro_far(
    score_matrix: np.ndarray,
    sid: int,
    threshold: float,
    y: np.ndarray,
    session: np.ndarray,
    within: np.ndarray,
    session_id: int,
) -> tuple[float, list[tuple[int, float, int]]]:
    matched = np.flatnonzero((y != sid) & (session == session_id) & (within == 10))
    if not len(matched):
        raise ValueError(f"No matched impostor checkpoints for session {session_id}")
    rows: list[tuple[int, float, int]] = []
    for source_id in np.unique(y[matched]):
        source_idx = matched[y[matched] == source_id]
        rate = float(np.mean(score_matrix[source_idx, sid] >= threshold))
        rows.append((int(source_id), rate, len(source_idx)))
    return float(np.mean([rate for _, rate, _ in rows])), rows


def endpoint_split(values: Sequence) -> tuple[np.ndarray, np.ndarray]:
    """First/last two checkpoints; validation tuning may contain only two."""
    array = np.asarray(values)
    if len(array) < 2:
        raise ValueError("Need at least two checkpoints")
    return array[:2], array[-2:]


def evaluate_tq_pairs(
    config: TQConfig,
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
    tq = TemporalQuarantineEMA(agent, enrollment, float(tau0), config, min_sigma)
    checkpoint_rows: list[dict] = []
    source_rows: list[dict] = []
    probe_rejections: list[bool] = []
    checkpoint_fars: list[float] = []
    adaptation_accepts = 0

    for checkpoint, (session_id, adaptation_index, probe_index) in enumerate(pairs):
        adaptation_score = float(genuine_scores[adaptation_index, sid])
        event = tq.process(adaptation_score, session_id)
        adaptation_accepts += int(event["authenticated"])
        profile = attack_v2.profile_snapshot(agent)
        probe_score = float(genuine_scores[probe_index, sid])
        accepted = probe_score >= profile.threshold
        probe_rejections.append(not accepted)
        checkpoint_far, sources = source_macro_far(
            impostor_score_matrix, sid, profile.threshold, y, session, within, session_id
        )
        checkpoint_fars.append(checkpoint_far)
        for source_id, rate, denominator in sources:
            source_rows.append({
                "checkpoint": checkpoint,
                "session": session_id,
                "source_id": source_id,
                "source_FAR": rate,
                "source_probe_n": denominator,
            })
        checkpoint_rows.append({
            "checkpoint": checkpoint,
            "session": session_id,
            "adaptation_index": adaptation_index,
            "probe_index": probe_index,
            "adaptation_score": adaptation_score,
            "probe_score": probe_score,
            "auth_threshold_before": event["threshold_before"],
            "update_threshold_before": event["update_threshold_before"],
            "threshold": profile.threshold,
            "mean": profile.mean,
            "sigma": profile.sigma,
            "adaptation_authenticated": event["authenticated"],
            "updated": event["updated"],
            "accepted": int(accepted),
            "checkpoint_FAR": checkpoint_far,
            "n_impostor_sources": len(sources),
            "updates_so_far": tq.trusted_updates + tq.recovery_updates,
            "event": event["event"],
            "transition_scale": event["transition_scale"],
            "recovery_target": event["recovery_target"],
            "quarantine_size_after": event["quarantine_size_after"],
        })

    after = attack_v2.profile_snapshot(agent)
    early_reject, late_reject = endpoint_split(probe_rejections)
    early_far_values, late_far_values = endpoint_split(checkpoint_fars)
    attempts = len(pairs)
    updates = tq.trusted_updates + tq.recovery_updates
    metrics = {
        "early_FRR": float(np.mean(early_reject)),
        "late_FRR": float(np.mean(late_reject)),
        "overall_FRR": float(np.mean(probe_rejections)),
        "early_FAR": float(np.mean(early_far_values)),
        "late_FAR": float(np.mean(late_far_values)),
        "overall_FAR": float(np.mean(checkpoint_fars)),
        "final_all_FAR": float(np.mean(
            impostor_score_matrix[np.flatnonzero(y != sid), sid] >= after.threshold
        )),
        "FAR": float(np.mean(late_far_values)),
        "HTER": 0.5 * (float(np.mean(late_reject)) + float(np.mean(late_far_values))),
        "adaptation_attempts": attempts,
        "adaptation_accepts": adaptation_accepts,
        "adaptation_auth_rate": adaptation_accepts / attempts,
        "genuine_updates": updates,
        "GUR": updates / attempts,
        "trusted_updates": tq.trusted_updates,
        "recovery_updates": tq.recovery_updates,
        "trusted_update_rate": tq.trusted_updates / attempts,
        "recovery_update_rate": tq.recovery_updates / attempts,
        "recovery_candidates": tq.recovery_candidates,
        "recovery_candidate_rate": tq.recovery_candidates / attempts,
        "recovery_confirmations": tq.recovery_confirmations,
        "recovery_confirmation_rate": tq.recovery_confirmations / attempts,
        "quarantine_resets": tq.quarantine_resets,
        "rejected_transitions": tq.rejected_transitions,
        "n_checkpoint_probes": attempts,
        "n_early_probes": len(early_reject),
        "n_late_probes": len(late_reject),
        "n_checkpoint_sessions": attempts,
        "non_stricter_gate_states": 0,
        "mu_enroll": tq.mu_enroll,
        "sigma_enroll": tq.sigma_enroll,
        **guard.profile_fields(before, after),
    }
    return metrics, checkpoint_rows, source_rows


def frozen_pair_metrics(
    sid: int,
    tau0: float,
    pairs: Sequence[tuple[int, int, int]],
    genuine_scores: np.ndarray,
    impostor_score_matrix: np.ndarray,
    y: np.ndarray,
    session: np.ndarray,
    within: np.ndarray,
) -> dict[str, float]:
    rejections: list[bool] = []
    fars: list[float] = []
    for session_id, _, probe_index in pairs:
        rejections.append(float(genuine_scores[probe_index, sid]) < tau0)
        far, _ = source_macro_far(
            impostor_score_matrix, sid, tau0, y, session, within, session_id
        )
        fars.append(far)
    _, late_reject = endpoint_split(rejections)
    _, late_far = endpoint_split(fars)
    frr = float(np.mean(late_reject))
    far = float(np.mean(late_far))
    return {"late_FRR": frr, "late_FAR": far, "HTER": 0.5 * (frr + far)}


def validation_split(
    sid: int,
    y: np.ndarray,
    session: np.ndarray,
    within: np.ndarray,
) -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int]]]:
    own = np.flatnonzero(y == sid)
    pairs = drift.session_pairs(own, session, within)
    enrollment_pairs = pairs[:2]
    tuning_pairs = pairs[2:]
    if len(tuning_pairs) < 2:
        raise ValueError("Need at least two held-out validation tuning sessions")
    return enrollment_pairs, tuning_pairs


def load_validation_payload(cache_dir: Path, fold: int) -> dict[str, np.ndarray]:
    path = cache_dir / f"fold{fold}_base.npz"
    required = {
        "X_val", "y_val", "session_val", "within_val", "val_scores"
    }
    with np.load(path) as archive:
        missing = required.difference(archive.files)
        if missing:
            raise KeyError(f"{path.name} missing validation fields: {sorted(missing)}")
        return {name: np.asarray(archive[name]) for name in required}


def load_validation_drift_scores(core, cache_dir: Path, fold: int,
                                 magnitude: float) -> tuple[np.ndarray, int]:
    """Predict drifted validation scores from the saved fold model; no retraining."""
    import torch

    payload = load_validation_payload(cache_dir, fold)
    score_path = cache_dir / f"fold{fold}_D{magnitude:.1f}.npz"
    with np.load(score_path) as archive:
        seed = int(np.asarray(archive["drift_seed"]).reshape(-1)[0])
    X_drift = core.inject_drift(
        payload["X_val"], payload["y_val"], payload["session_val"],
        payload["within_val"], magnitude=float(magnitude), seed=seed,
    )
    model_path = cache_dir / f"fold{fold}_model.pt"
    try:
        checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
    except TypeError:
        checkpoint = torch.load(model_path, map_location="cpu")
    model = core.LSTMAuth(int(checkpoint["n_features"]), int(checkpoint["n_classes"]))
    model.load_state_dict(checkpoint["state_dict"])
    model.to(torch.device("cpu"))
    scores = core.predict_lstm(model, X_drift, torch.device("cpu")).astype(np.float64)
    return scores, seed


def select_validation_config(candidate_summary: pd.DataFrame) -> pd.Series:
    frame = candidate_summary.copy()
    frame["feasible"] = frame["late_FAR_change"] <= VALIDATION_FAR_LIMIT + 1e-12
    feasible = frame[frame["feasible"]]
    if not len(feasible):
        raise RuntimeError(
            "No TQ-EMA configuration satisfies the preregistered validation "
            "Delta-FAR <= +1 percentage-point constraint"
        )
    # The final four fields are the prespecified conservative exact-tie rule.
    ordered = feasible.sort_values(
        [
            "late_FRR_gain", "confirmation_sessions", "band_sigma",
            "recovery_alpha", "anchor_sigma", "config_id",
        ],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    )
    selected = ordered.iloc[0].copy()
    selected["selection_status"] = "feasible"
    return selected


def tune_fold(
    fold: int,
    cache_dir: Path,
    core,
    attack_v2,
    max_subjects: int | None,
) -> tuple[TQConfig, pd.DataFrame, pd.DataFrame, dict]:
    payload = load_validation_payload(cache_dir, fold)
    drift_scores, drift_seed = load_validation_drift_scores(
        core, cache_dir, fold, VALIDATION_DRIFT
    )
    y = payload["y_val"]
    session = payload["session_val"]
    within = payload["within_val"]
    clean_scores = payload["val_scores"].astype(np.float64)
    configs = tq_grid()
    rows: list[dict] = []
    exclusions: list[dict] = []
    n_subjects = clean_scores.shape[1]
    subject_ids = range(n_subjects if max_subjects is None else min(max_subjects, n_subjects))

    for sid in subject_ids:
        try:
            enrollment_pairs, tuning_pairs = validation_split(sid, y, session, within)
        except ValueError as exc:
            exclusions.append({"fold": fold, "sid": sid, "reason": str(exc)})
            continue
        enrollment_indices = np.asarray(
            [index for _, adapt, probe in enrollment_pairs for index in (adapt, probe)],
            dtype=np.int64,
        )
        enrollment = clean_scores[enrollment_indices, sid]
        enrollment_sessions = {session_id for session_id, _, _ in enrollment_pairs}
        impostor_indices = np.flatnonzero(
            (y != sid) & np.isin(session, list(enrollment_sessions))
        )
        validation_impostor = clean_scores[impostor_indices, sid]
        if len(enrollment) < 2 or not len(validation_impostor):
            exclusions.append({
                "fold": fold, "sid": sid,
                "reason": "insufficient inner enrollment or impostor calibration",
            })
            continue
        _, tau0 = core.eer_from_scores(enrollment, validation_impostor)
        frozen = frozen_pair_metrics(
            sid, float(tau0), tuning_pairs, drift_scores, clean_scores,
            y, session, within,
        )
        for config in configs:
            metrics, _, _ = evaluate_tq_pairs(
                config, sid, float(tau0), enrollment, tuning_pairs,
                drift_scores, clean_scores, y, session, within, core, attack_v2,
            )
            rows.append({
                "fold": fold, "sid": sid, "config_id": config.config_id,
                **asdict(config),
                "late_FRR": metrics["late_FRR"],
                "late_FAR": metrics["late_FAR"],
                "HTER": metrics["HTER"],
                "frozen_late_FRR": frozen["late_FRR"],
                "frozen_late_FAR": frozen["late_FAR"],
                "frozen_HTER": frozen["HTER"],
                "late_FRR_gain": frozen["late_FRR"] - metrics["late_FRR"],
                "late_FAR_change": metrics["late_FAR"] - frozen["late_FAR"],
                "HTER_change": metrics["HTER"] - frozen["HTER"],
                "GUR": metrics["GUR"],
                "recovery_candidate_rate": metrics["recovery_candidate_rate"],
                "recovery_update_rate": metrics["recovery_update_rate"],
            })

    subject_frame = pd.DataFrame(rows)
    if subject_frame.empty:
        raise RuntimeError(f"Fold {fold}: no eligible validation subjects")
    keys = ["config_id"] + list(asdict(configs[0]).keys())
    metrics = [
        "late_FRR", "late_FAR", "HTER", "frozen_late_FRR",
        "frozen_late_FAR", "frozen_HTER", "late_FRR_gain",
        "late_FAR_change", "HTER_change", "GUR",
        "recovery_candidate_rate", "recovery_update_rate",
    ]
    summary = subject_frame.groupby(keys, as_index=False)[metrics].mean()
    counts = subject_frame.groupby(keys, as_index=False).agg(n_subjects=("sid", "nunique"))
    summary = summary.merge(counts, on=keys)
    selected = select_validation_config(summary)
    config = TQConfig(
        band_sigma=float(selected["band_sigma"]),
        confirmation_sessions=int(selected["confirmation_sessions"]),
        recovery_alpha=float(selected["recovery_alpha"]),
        anchor_sigma=float(selected["anchor_sigma"]),
    )
    metadata = {
        "fold": fold,
        "validation_drift": VALIDATION_DRIFT,
        "validation_drift_seed": drift_seed,
        "selection_status": str(selected["selection_status"]),
        "selected_config_id": config.config_id,
        "selected_validation_late_FRR_gain": float(selected["late_FRR_gain"]),
        "selected_validation_late_FAR_change": float(selected["late_FAR_change"]),
        "selected_validation_HTER_change": float(selected["HTER_change"]),
        "n_validation_subjects": int(selected["n_subjects"]),
        "n_validation_exclusions": len(exclusions),
    }
    return config, subject_frame, summary, {"metadata": metadata, "exclusions": exclusions}


def baseline_policies() -> list[guard.Policy]:
    return [
        guard.Policy("frozen", "Frozen", -1.0),
        guard.Policy("blind", "Blind EMA", -1.0),
        guard.Policy("guarded_0.25", "Guarded EMA", 0.25),
        guard.Policy("oracle_all", "Oracle-all-genuine", -1.0),
    ]


def source_rows_from_checkpoints(
    checkpoint_rows: Sequence[dict],
    sid: int,
    score_matrix: np.ndarray,
    y: np.ndarray,
    session: np.ndarray,
    within: np.ndarray,
) -> list[dict]:
    rows: list[dict] = []
    for checkpoint in checkpoint_rows:
        _, sources = source_macro_far(
            score_matrix, sid, float(checkpoint["threshold"]), y, session, within,
            int(checkpoint["session"]),
        )
        for source_id, rate, denominator in sources:
            rows.append({
                "checkpoint": int(checkpoint["checkpoint"]),
                "session": int(checkpoint["session"]),
                "source_id": source_id,
                "source_FAR": rate,
                "source_probe_n": denominator,
            })
    return rows


def percentage_export(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    columns = [
        column for column in out.columns
        if column in RATE_COLUMNS
        or (column.endswith("_subject_sd") and column.removesuffix("_subject_sd") in RATE_COLUMNS)
        or column in {
            "selected_validation_late_FRR_gain",
            "selected_validation_late_FAR_change",
            "selected_validation_HTER_change",
        }
    ]
    if columns:
        out[columns] = 100.0 * out[columns]
    return out


def two_way_far_bootstrap(source_rows: pd.DataFrame, n_bootstrap: int,
                          seed: int) -> pd.DataFrame:
    """Independent victim/source resampling for the primary D=2 FAR contrast."""
    frame = source_rows[
        (source_rows["D"] == 2.0)
        & source_rows["policy_id"].isin(["frozen", "tq_ema"])
    ].copy()
    max_checkpoint = frame.groupby(["fold", "sid", "policy_id"])["checkpoint"].transform("max")
    frame = frame[frame["checkpoint"] >= max_checkpoint - 1]
    pair = frame.groupby(
        ["sid", "source_id", "policy_id"], as_index=False
    )["source_FAR"].mean()
    pivot = pair.pivot_table(
        index=["sid", "source_id"], columns="policy_id", values="source_FAR"
    ).dropna()
    if not {"frozen", "tq_ema"}.issubset(pivot.columns):
        return pd.DataFrame()
    pivot["difference"] = pivot["tq_ema"] - pivot["frozen"]
    victims = np.sort(pivot.index.get_level_values("sid").unique())
    sources = np.sort(pivot.index.get_level_values("source_id").unique())
    vi = {value: index for index, value in enumerate(victims)}
    si = {value: index for index, value in enumerate(sources)}
    matrix = np.full((len(victims), len(sources)), np.nan, dtype=float)
    for (victim, source), value in pivot["difference"].items():
        matrix[vi[victim], si[source]] = float(value)
    finite = np.isfinite(matrix).astype(float)
    values = np.nan_to_num(matrix, nan=0.0)
    rng = np.random.default_rng(seed)
    draws: list[np.ndarray] = []
    chunk_size = 250
    for start in range(0, n_bootstrap, chunk_size):
        count = min(chunk_size, n_bootstrap - start)
        victim_draws = rng.integers(0, len(victims), size=(count, len(victims)))
        source_draws = rng.integers(0, len(sources), size=(count, len(sources)))
        victim_weights = np.apply_along_axis(
            lambda x: np.bincount(x, minlength=len(victims)), 1, victim_draws
        ).astype(float)
        source_weights = np.apply_along_axis(
            lambda x: np.bincount(x, minlength=len(sources)), 1, source_draws
        ).astype(float)
        numerator = np.einsum("bi,ij,bj->b", victim_weights, values, source_weights)
        denominator = np.einsum("bi,ij,bj->b", victim_weights, finite, source_weights)
        draws.append(numerator / denominator)
    samples = np.concatenate(draws)
    return pd.DataFrame([{
        "scenario": "claimant_only",
        "D": 2.0,
        "contrast": "TQ-EMA minus Frozen late FAR",
        "n_victims": len(victims),
        "n_impostor_sources": len(sources),
        "n_victim_source_pairs": int(np.isfinite(matrix).sum()),
        "n_bootstrap": n_bootstrap,
        "estimate": float(np.nanmean(matrix)),
        "ci95_low": float(np.quantile(samples, 0.025)),
        "ci95_high": float(np.quantile(samples, 0.975)),
    }])


def save_trajectory_plots(checkpoints: pd.DataFrame, output_dir: Path) -> None:
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    methods = ["Frozen", "Blind EMA", "Guarded EMA", "Oracle-all-genuine", "TQ-EMA"]
    colors = {
        "Frozen": "#4b5563", "Blind EMA": "#d97706", "Guarded EMA": "#2563eb",
        "Oracle-all-genuine": "#059669", "TQ-EMA": "#be123c",
    }
    frame = checkpoints.copy()
    path_keys = ["fold", "D", "sid", "policy_id"]
    frame["path_length"] = frame.groupby(path_keys)["checkpoint"].transform("size")
    frame = frame[frame["path_length"] == 5]
    for drift_value, group in frame.groupby("D", sort=True):
        n_paths = group[["fold", "sid"]].drop_duplicates().shape[0]
        aggregate = group.groupby(["method", "checkpoint"], as_index=False).agg(
            adaptation_score=("adaptation_score", "mean"),
            probe_score=("probe_score", "mean"),
            threshold=("threshold", "mean"),
            mean=("mean", "mean"), sigma=("sigma", "mean"),
            auth_rate=("adaptation_authenticated", "mean"),
            update_rate=("updated", "mean"),
        )
        score_path = group.groupby("checkpoint", as_index=False).agg(
            adaptation_score=("adaptation_score", "mean"),
            probe_score=("probe_score", "mean"),
        )
        fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.2), constrained_layout=True)
        ax = axes[0, 0]
        x = score_path["checkpoint"] + 1
        ax.plot(x, score_path["adaptation_score"], color="#111827", marker="o",
                linewidth=2.2, label="Genuine adaptation score")
        ax.plot(x, score_path["probe_score"], color="#7c3aed", marker="s",
                linewidth=2.2, label="Genuine checkpoint score")
        for method in methods:
            values = aggregate[aggregate["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, values["threshold"],
                        color=colors[method], linewidth=1.8, label=f"{method} threshold")
        ax.set(title=f"Scores and thresholds (D={drift_value:g})",
               xlabel="Session checkpoint", ylabel="LSTM claimant score")
        ax.legend(fontsize=7.6, ncol=2)

        ax = axes[0, 1]
        for method in methods:
            values = aggregate[aggregate["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, values["mean"], marker="o",
                        color=colors[method], label=method)
        ax.set(title="EMA profile mean", xlabel="Session checkpoint", ylabel="Mean score")
        ax.legend(fontsize=8)

        ax = axes[1, 0]
        for method in methods:
            values = aggregate[aggregate["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, values["sigma"], marker="o",
                        color=colors[method], label=method)
        ax.set(title="EMA profile sigma", xlabel="Session checkpoint", ylabel="Sigma")
        ax.legend(fontsize=8)

        ax = axes[1, 1]
        for method in methods:
            values = aggregate[aggregate["method"] == method]
            if len(values):
                ax.plot(values["checkpoint"] + 1, 100 * values["auth_rate"],
                        color=colors[method], linestyle="--", linewidth=1.3)
                ax.plot(values["checkpoint"] + 1, 100 * values["update_rate"],
                        color=colors[method], marker="o", linewidth=2,
                        label=f"{method} update")
        ax.set(title="Authentication (dashed) and production updates",
               xlabel="Session checkpoint", ylabel="Rate (%)", ylim=(-2, 102))
        ax.legend(fontsize=7.5)
        for axis in axes.flat:
            axis.grid(alpha=0.25)
        fig.suptitle(
            f"Claimant-only clean drift, D={drift_value:g} "
            f"({n_paths} complete subject-fold paths)", fontsize=14,
        )
        fig.savefig(figure_dir / f"tq_trajectory_claimant_only_D{drift_value:.1f}.png", dpi=180)
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
    return Path("results") / f"{datetime.now():%Y%m%d-%H%M%S}-tq-clean-drift"


def primary_assessment(summary: pd.DataFrame, bootstrap: pd.DataFrame) -> dict:
    all_frr = bootstrap[
        (bootstrap["cohort"] == "all_available_folds")
        & (bootstrap["D"] == 2.0)
        & (bootstrap["policy_id"] == "tq_ema")
        & (bootstrap["effect"] == "late_FRR_gain")
    ].iloc[0]
    complete_frr = bootstrap[
        (bootstrap["cohort"].str.startswith("complete_case"))
        & (bootstrap["D"] == 2.0)
        & (bootstrap["policy_id"] == "tq_ema")
        & (bootstrap["effect"] == "late_FRR_gain")
    ].iloc[0]
    # Summary already contains Frozen-relative gains but not Frozen FAR, so use
    # the paired bootstrap estimate for the subject-macro FAR change.
    far_row = bootstrap[
        (bootstrap["cohort"] == "all_available_folds")
        & (bootstrap["D"] == 2.0)
        & (bootstrap["policy_id"] == "tq_ema")
        & (bootstrap["effect"] == "late_FAR_change")
    ].iloc[0]
    hter_gain = bootstrap[
        (bootstrap["cohort"] == "all_available_folds")
        & (bootstrap["D"] == 2.0)
        & (bootstrap["policy_id"] == "tq_ema")
        & (bootstrap["effect"] == "HTER_gain")
    ].iloc[0]
    far_change = float(far_row["estimate"])
    hter_change = -float(hter_gain["estimate"])
    return {
        "scenario": "claimant_only",
        "D": 2.0,
        "primary_comparison": "TQ-EMA versus Frozen",
        "late_FRR_gain": float(all_frr["estimate"]),
        "late_FRR_gain_ci95_low": float(all_frr["ci95_low"]),
        "late_FRR_gain_ci95_high": float(all_frr["ci95_high"]),
        "late_FAR_change": far_change,
        "HTER_change": hter_change,
        "complete_case_late_FRR_gain_ci95_low": float(complete_frr["ci95_low"]),
        "criterion_frr_ci_above_zero": bool(float(all_frr["ci95_low"]) > 0.0),
        "criterion_far_change_at_most_1pp": bool(far_change <= VALIDATION_FAR_LIMIT),
        "criterion_hter_degradation_at_most_0_5pp": bool(hter_change <= TEST_HTER_LIMIT),
        "criterion_complete_case_preserved": bool(float(complete_frr["ci95_low"]) > 0.0),
    }


def run(args: argparse.Namespace) -> Path:
    source_dir = Path(args.source_dir).resolve()
    cache_dir = Path(args.cache_dir).resolve() if args.cache_dir else source_dir / "paper3_cache"
    output_dir = resolve_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    core, attack_v2 = guard.load_canonical_modules(source_dir)
    folds = tuple(args.folds)
    n_canonical_folds = int(getattr(core, "N_FOLDS", 5))
    if any(fold < 1 or fold > n_canonical_folds for fold in folds):
        raise ValueError(f"Fold IDs must be within 1..{n_canonical_folds}")

    config_payload = {
        "source_dir": str(source_dir), "cache_dir": str(cache_dir),
        "folds": list(folds), "max_subjects": args.max_subjects,
        "drifts": list(args.drifts), "scenario": "claimant_only",
        "validation_drift": VALIDATION_DRIFT,
        "validation_split": "first 2 complete sessions enrollment; remaining sessions tuning",
        "validation_far_limit": VALIDATION_FAR_LIMIT,
        "tq_grid": [asdict(config) for config in tq_grid()],
        "selection_rule": (
            "maximize validation late-FRR gain among configs with Delta FAR <= 0.01; "
            "exact ties prefer larger m, narrower band, lower alpha, tighter anchor"
        ),
        "primary_test": "claimant-only D=2, TQ-EMA versus Frozen late-FRR gain",
        "test_hter_degradation_limit": TEST_HTER_LIMIT,
        "bootstrap_replicates": args.bootstrap_replicates,
        "bootstrap_seed": args.seed,
        "two_way_far_bootstrap": "independent victim and impostor-source resampling",
    }
    (output_dir / "config.json").write_text(
        json.dumps(config_payload, indent=2) + "\n", encoding="utf-8"
    )
    status = "running"
    log: list[str] = []

    try:
        selected_configs: dict[int, TQConfig] = {}
        validation_subject_frames: list[pd.DataFrame] = []
        validation_summary_frames: list[pd.DataFrame] = []
        selection_rows: list[dict] = []
        exclusions: list[dict] = []

        # Complete validation-only selection before loading any held-out test scores.
        for fold in folds:
            selected, subject_frame, candidate_summary, details = tune_fold(
                fold, cache_dir, core, attack_v2, args.max_subjects
            )
            selected_configs[fold] = selected
            validation_subject_frames.append(subject_frame)
            validation_summary_frames.append(candidate_summary)
            selection_rows.append({**details["metadata"], **asdict(selected)})
            exclusions.extend(
                {"stage": "validation", **row} for row in details["exclusions"]
            )
            message = f"Fold {fold}: selected {selected.config_id} on validation only"
            print(message, flush=True)
            log.append(message)

        validation_subject = pd.concat(validation_subject_frames, ignore_index=True)
        validation_candidates = pd.concat(validation_summary_frames, ignore_index=True)
        selected_frame = pd.DataFrame(selection_rows)
        percentage_export(validation_subject).to_csv(
            output_dir / "paper3_tq_validation_subject.csv", index=False
        )
        percentage_export(validation_candidates).to_csv(
            output_dir / "paper3_tq_validation_candidates.csv", index=False
        )
        percentage_export(selected_frame).to_csv(
            output_dir / "paper3_tq_selected_by_fold.csv", index=False
        )

        rows: list[dict] = []
        checkpoints: list[dict] = []
        source_far_rows: list[dict] = []
        policies = baseline_policies()

        for fold in folds:
            clean = attack_v2.load_fold(cache_dir, fold, drift=0.0)
            selected = selected_configs[fold]
            val_scores, y_val = clean["val_scores"], clean["y_val"]
            y_test = clean["y_test"]
            session_test, within_test = clean["session_test"], clean["within_test"]
            clean_scores = clean["test_scores"]
            for drift_value in args.drifts:
                drifted = attack_v2.load_fold(cache_dir, fold, drift=drift_value)
                for field in ("y_test", "session_test", "within_test"):
                    if not np.array_equal(clean[field], drifted[field]):
                        raise AssertionError(
                            f"Cache alignment failed for fold={fold}, D={drift_value}, {field}"
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
                    if len(enrollment) < 2 or not len(validation_impostor):
                        exclusions.append({
                            "stage": "test", "fold": fold, "D": drift_value,
                            "sid": sid, "reason": "insufficient enrollment/calibration",
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
                            "selected_config_id": selected.config_id,
                        }
                        rows.append({**identity, **metrics})
                        checkpoints.extend({**identity, **probe} for probe in probe_rows)
                        if float(drift_value) == 2.0 and policy.policy_id == "frozen":
                            sources = source_rows_from_checkpoints(
                                probe_rows[-2:], sid, clean_scores, y_test,
                                session_test, within_test,
                            )
                            source_far_rows.extend({**identity, **source} for source in sources)

                    tq_metrics, tq_checkpoints, tq_sources = evaluate_tq_pairs(
                        selected, sid, float(tau0), enrollment, pairs, drift_scores,
                        clean_scores, y_test, session_test, within_test, core, attack_v2,
                    )
                    tq_identity = {
                        "fold": fold, "scenario": "claimant_only", "D": float(drift_value),
                        "sid": sid, "policy_id": "tq_ema", "method": "TQ-EMA",
                        "lambda": f"{TRUSTED_LAMBDA:.2f}",
                        "lambda_value": TRUSTED_LAMBDA, "tau0": float(tau0),
                        "selected_config_id": selected.config_id,
                    }
                    rows.append({**tq_identity, **tq_metrics})
                    checkpoints.extend({**tq_identity, **probe} for probe in tq_checkpoints)
                    if float(drift_value) == 2.0:
                        first_late = len(pairs) - 2
                        source_far_rows.extend(
                            {**tq_identity, **source}
                            for source in tq_sources
                            if int(source["checkpoint"]) >= first_late
                        )

            message = f"Fold {fold}: held-out test complete"
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
        complete_label = f"complete_case_{len(folds)}_folds"
        bootstrap_complete.insert(0, "cohort", complete_label)
        bootstrap = pd.concat([bootstrap_all, bootstrap_complete], ignore_index=True)
        source_frame = pd.DataFrame(source_far_rows)
        two_way = two_way_far_bootstrap(source_frame, args.bootstrap_replicates, args.seed + 911)
        assessment = primary_assessment(summary, bootstrap)

        percentage_export(subject_fold).to_csv(
            output_dir / "paper3_tq_subject_fold.csv", index=False
        )
        percentage_export(by_fold).to_csv(
            output_dir / "paper3_tq_by_fold_descriptive.csv", index=False
        )
        percentage_export(by_subject).to_csv(
            output_dir / "paper3_tq_by_subject.csv", index=False
        )
        percentage_export(summary).to_csv(
            output_dir / "paper3_tq_summary.csv", index=False
        )
        checkpoint_frame = pd.DataFrame(checkpoints)
        percentage_export(checkpoint_frame).to_csv(
            output_dir / "paper3_tq_checkpoints.csv", index=False
        )
        percentage_export(source_frame).to_csv(
            output_dir / "paper3_tq_source_far.csv.gz", index=False,
            compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
        )
        bootstrap_export = bootstrap.copy()
        bootstrap_export[["estimate", "ci95_low", "ci95_high"]] *= 100.0
        bootstrap_export.to_csv(
            output_dir / "paper3_tq_paired_subject_bootstrap.csv", index=False
        )
        if len(two_way):
            two_way_export = two_way.copy()
            two_way_export[["estimate", "ci95_low", "ci95_high"]] *= 100.0
            two_way_export.to_csv(
                output_dir / "paper3_tq_two_way_far_bootstrap.csv", index=False
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
        print("\nTQ clean-drift summary (subject macro means):")
        print(display.round(5).to_string(index=False))
        print("\nPrimary assessment:")
        print(json.dumps(assessment_export, indent=2))
        log.extend(["", display.round(5).to_string(index=False), "", json.dumps(assessment_export, indent=2)])
        status = "complete"
        return output_dir
    finally:
        (output_dir / "run.log").write_text("\n".join(log) + "\n", encoding="utf-8")
        source_hashes = {}
        for name in [
            "hmog_revised_experiment.py", "paper3_poisoning_attack_v2.py",
            "paper3_guarded_adaptation.py", "paper3_guarded_drift.py",
        ]:
            if name == "paper3_guarded_adaptation.py":
                path = Path(guard.__file__).resolve()
            elif name == "paper3_guarded_drift.py":
                path = Path(drift.__file__).resolve()
            elif name == "hmog_revised_experiment.py":
                path = Path(core.__file__).resolve()
            elif name == "paper3_poisoning_attack_v2.py":
                path = Path(attack_v2.__file__).resolve()
            else:
                path = source_dir / name
            if path.is_file():
                source_hashes[name] = sha256(path)
        source_hashes[Path(__file__).name] = sha256(Path(__file__).resolve())
        cache_hashes = {}
        for fold in folds:
            for suffix in ["base.npz", "model.pt"] + [f"D{value:.1f}.npz" for value in args.drifts]:
                path = cache_dir / f"fold{fold}_{suffix}"
                if path.is_file():
                    cache_hashes[path.name] = sha256(path)
        manifest = {
            "status": status,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "command": shlex.join(sys.argv), "python": sys.version,
            "platform": platform.platform(), "source_hashes": source_hashes,
            "cache_hashes": cache_hashes,
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def parse_folds(text: str) -> tuple[int, ...]:
    try:
        values = tuple(sorted({int(item.strip()) for item in text.split(",")}))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected comma-separated fold IDs") from exc
    if not values:
        raise argparse.ArgumentTypeError("Fold list cannot be empty")
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=".")
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--drifts", type=drift.parse_drifts, default=DEFAULT_DRIFTS)
    parser.add_argument("--folds", type=parse_folds, default=(1, 2, 3, 4, 5))
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
    print(f"\nSaved TQ-EMA clean-drift run: {destination.resolve()}")
