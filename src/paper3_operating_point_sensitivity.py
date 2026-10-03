#!/usr/bin/env python3
"""Locked operating-point sensitivity analysis for Paper 3.

This runner consumes frozen HMOG and McGill score caches.  It never trains a
model or generates scores.  See experiments/paper3_operating_point_sensitivity.*
for the prospectively frozen protocol.
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
import subprocess
import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


PROTOCOL_ID = "paper3-operating-point-sensitivity-v1"
CONDITIONS = ("reference", "far_5pct", "far_1pct")
TARGETS = {"reference": None, "far_5pct": 0.05, "far_1pct": 0.01}
METHODS = ("Frozen", "Blind EMA", "Guarded EMA")
STRATEGIES = ("random", "boundary")
BUDGETS = (0, 1, 2, 4, 8)
MAX_BUDGET = 8
RATE_METRICS = {
    "post_ASR", "post_FRR", "HTER", "poison_accept_rate", "MUR",
    "tau_auth_ge_mu_fraction", "gate_stricter_state_fraction",
    "accepted_blocked_by_gate_rate",
}
SUMMARY_METRICS = (
    "post_ASR", "post_FRR", "HTER", "poison_accept_rate", "MUR",
    "malicious_updates", "mean_delta", "sigma_delta", "threshold_delta",
)
REFERENCE_METRICS = (
    "post_ASR", "post_FRR", "HTER", "poison_accept_rate", "MUR",
    "malicious_updates", "mean_delta", "sigma_delta", "threshold_delta",
    "threshold_before", "threshold_after",
)
REFERENCE_TOLERANCE = 1e-9


class ProtocolError(RuntimeError):
    """Raised when a frozen invariant is violated."""


class BoundaryInfeasible(RuntimeError):
    """Raised when a boundary sequence cannot reach the requested budget."""


@dataclass(frozen=True)
class Calibration:
    condition: str
    target: float | None
    tau_ref: float
    tau0: float
    achieved_far: float
    calibration_frr: float
    reference_retained: bool
    n_genuine: int
    n_impostor: int
    n_impostor_identities: int
    mu0: float
    sigma0: float
    k: float


@dataclass(frozen=True)
class Snapshot:
    mean: float
    sigma: float
    threshold: float


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_indices(values: Sequence[int] | np.ndarray) -> str:
    array = np.asarray(values, dtype="<i8")
    return hashlib.sha256(array.tobytes()).hexdigest()


def assert_disjoint_pools(poison_pool: Sequence[int], probe_pool: Sequence[int]) -> None:
    overlap = np.intersect1d(
        np.asarray(poison_pool, dtype=np.int64),
        np.asarray(probe_pool, dtype=np.int64),
        assume_unique=False,
    )
    if overlap.size:
        raise ProtocolError(f"Poison/probe leakage: {overlap.size} overlapping indices")


def stable_seed(master: int, *parts: object) -> int:
    payload = "|".join(map(str, parts)).encode("utf-8")
    return int(np.random.SeedSequence([master, int(hashlib.sha256(payload).hexdigest()[:8], 16)]).generate_state(1)[0])


def git_revision(project_dir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project_dir, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def load_modules(project_dir: Path):
    source = project_dir / "src"
    sys.path.insert(0, str(source))
    try:
        core = importlib.import_module("hmog_revised_experiment")
        attack = importlib.import_module("paper3_poisoning_attack_v2")
        mcgill = importlib.import_module("paper3_external_mcgill")
    finally:
        sys.path.pop(0)
    return core, attack, mcgill


def verify_protocol_and_inputs(project_dir: Path, protocol_path: Path, mcgill_cache: Path) -> dict[str, str]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("protocol_id") != PROTOCOL_ID:
        raise ProtocolError("Unexpected protocol id")
    actual: dict[str, str] = {}
    for name, expected in protocol["datasets"]["HMOG"]["cache_sha256"].items():
        path = project_dir / "paper3_cache" / name
        if not path.is_file():
            raise ProtocolError(f"Missing HMOG cache: {path}")
        observed = sha256_file(path)
        if observed != expected:
            raise ProtocolError(f"HMOG cache hash mismatch: {name}")
        actual[str(path)] = observed
    expected_mcgill = protocol["datasets"]["McGill"]["cache_sha256"]
    if not mcgill_cache.is_file():
        raise ProtocolError(f"Missing McGill cache: {mcgill_cache}")
    observed_mcgill = sha256_file(mcgill_cache)
    if observed_mcgill != expected_mcgill:
        raise ProtocolError("McGill cache hash mismatch")
    actual[str(mcgill_cache)] = observed_mcgill
    for relative, expected in protocol["authoritative_source_sha256"].items():
        path = project_dir / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise ProtocolError(f"Authoritative source mismatch: {relative}")
    return actual


def select_target_threshold(reference_threshold: float, impostor_scores: Sequence[float], target: float) -> float:
    """Return the most permissive finite float64 threshold satisfying target."""
    reference = np.float64(reference_threshold)
    impostor = np.asarray(impostor_scores, dtype=np.float64)
    if impostor.size == 0 or not np.all(np.isfinite(impostor)):
        raise ProtocolError("Calibration impostor scores must be finite and non-empty")
    if not 0.0 <= target <= 1.0:
        raise ValueError("target must be in [0, 1]")
    if float(np.mean(impostor >= reference)) <= target:
        return float(reference)
    stepped = np.nextafter(np.unique(impostor), np.float64(np.inf))
    candidates = stepped[(stepped >= reference) & np.isfinite(stepped)]
    for candidate in candidates:
        if float(np.mean(impostor >= candidate)) <= target:
            return float(candidate)
    raise ProtocolError("No finite threshold candidate satisfies calibration FAR target")


def calibration_record(
    condition: str,
    genuine: Sequence[float],
    impostor: Sequence[float],
    impostor_identities: Sequence[int],
    reference_threshold: float,
    min_sigma: float,
) -> Calibration:
    genuine_array = np.asarray(genuine, dtype=np.float64)
    impostor_array = np.asarray(impostor, dtype=np.float64)
    if genuine_array.size < 2 or impostor_array.size == 0:
        raise ProtocolError("Insufficient calibration observations")
    target = TARGETS[condition]
    tau0 = float(reference_threshold) if target is None else select_target_threshold(reference_threshold, impostor_array, target)
    mu0 = float(np.mean(genuine_array))
    second = float(np.mean(genuine_array * genuine_array))
    sigma0 = math.sqrt(max(second - mu0 * mu0, min_sigma * min_sigma))
    k = (mu0 - tau0) / sigma0
    return Calibration(
        condition=condition,
        target=target,
        tau_ref=float(reference_threshold),
        tau0=tau0,
        achieved_far=float(np.mean(impostor_array >= tau0)),
        calibration_frr=float(np.mean(genuine_array < tau0)),
        reference_retained=bool(tau0 == float(reference_threshold)),
        n_genuine=int(genuine_array.size),
        n_impostor=int(impostor_array.size),
        n_impostor_identities=int(np.unique(np.asarray(impostor_identities)).size),
        mu0=mu0,
        sigma0=sigma0,
        k=float(k),
    )


def calibration_to_row(dataset: str, fold: int, victim: int, item: Calibration) -> dict[str, object]:
    return {
        "dataset": dataset,
        "fold": fold,
        "victim": victim,
        "condition": item.condition,
        "nominal_calibration_far": item.target,
        "n_genuine_calibration": item.n_genuine,
        "n_impostor_calibration": item.n_impostor,
        "n_impostor_identities": item.n_impostor_identities,
        "empirical_far_resolution": 1.0 / item.n_impostor,
        "reference_threshold": item.tau_ref,
        "initial_threshold": item.tau0,
        "achieved_calibration_far": item.achieved_far,
        "calibration_frr": item.calibration_frr,
        "reference_retained": item.reference_retained,
        "mu0": item.mu0,
        "sigma0": item.sigma0,
        "k": item.k,
        "k_sign": "negative" if item.k < 0 else ("positive" if item.k > 0 else "zero"),
        "initial_tau_ge_mu": bool(item.tau0 >= item.mu0),
        "initial_update_threshold_raw": item.tau0 + 0.25 * (item.mu0 - item.tau0),
        "initial_update_threshold_effective": max(item.tau0, item.tau0 + 0.25 * (item.mu0 - item.tau0)),
    }


def profile_snapshot(dataset: str, profile: object, attack_module) -> Snapshot:
    if dataset == "HMOG":
        state = attack_module.profile_snapshot(profile)
        return Snapshot(state.mean, state.sigma, state.threshold)
    return Snapshot(float(profile.mu), float(profile.sigma), float(profile.threshold))


def make_profile(dataset: str, enrollment: np.ndarray, threshold: float, core, mcgill):
    if dataset == "HMOG":
        return core.AdaptiveEMA.from_enrollment(enrollment, threshold)
    return mcgill.EMAProfile.from_enrollment(
        enrollment, threshold, alpha=0.05, min_sigma=1e-4,
    )


def update_profile(dataset: str, profile: object, score: float) -> None:
    if dataset == "HMOG":
        if not bool(profile.decide(score)):
            raise ProtocolError("Canonical HMOG profile rejected an authorized update")
    else:
        profile.update(score)


def probe_rate(scores: Sequence[float], threshold: float) -> float:
    values = np.asarray(scores, dtype=np.float64)
    if values.size == 0:
        raise ProtocolError("Probe set is empty")
    return float(np.mean(values >= threshold))


def evaluate_method(
    dataset: str,
    method: str,
    enrollment: np.ndarray,
    calibration: Calibration,
    poison_scores: np.ndarray,
    probe_scores: np.ndarray,
    genuine_scores: np.ndarray,
    core,
    attack_module,
    mcgill,
) -> tuple[dict[str, object], object]:
    profile = make_profile(dataset, enrollment, calibration.tau0, core, mcgill)
    before = profile_snapshot(dataset, profile, attack_module)
    if not np.isclose(before.threshold, calibration.tau0, atol=1e-14, rtol=0.0):
        raise ProtocolError("Adaptive and Frozen starting thresholds differ")
    mu_enroll = calibration.mu0
    poison_accepts = updates = 0
    gate_states = gate_strict = tau_ge_mu = accepted_blocked = 0
    for raw in np.asarray(poison_scores, dtype=np.float64):
        score = float(raw)
        tau_auth = float(profile.threshold)
        authenticated = score >= tau_auth
        poison_accepts += int(authenticated)
        update = False
        if method == "Blind EMA":
            update = authenticated
        elif method == "Guarded EMA":
            raw_gate = tau_auth + 0.25 * (mu_enroll - tau_auth)
            effective_gate = max(tau_auth, raw_gate)
            gate_states += 1
            strict = effective_gate > tau_auth
            gate_strict += int(strict)
            tau_ge_mu += int(tau_auth >= mu_enroll)
            update = authenticated and score >= raw_gate
            accepted_blocked += int(authenticated and not update)
        elif method != "Frozen":
            raise ValueError(f"Unknown method: {method}")
        if update:
            update_profile(dataset, profile, score)
            updates += 1
    after = profile_snapshot(dataset, profile, attack_module)
    asr = probe_rate(probe_scores, after.threshold)
    frr = float(np.mean(np.asarray(genuine_scores, dtype=np.float64) < after.threshold))
    raw_initial = calibration.tau0 + 0.25 * (mu_enroll - calibration.tau0)
    effective_initial = max(calibration.tau0, raw_initial)
    denominator = len(poison_scores)
    row = {
        "method": method,
        "post_ASR": asr,
        "post_FRR": frr,
        "HTER": 0.5 * (asr + frr),
        "poison_accepts": poison_accepts,
        "poison_accept_rate": poison_accepts / denominator if denominator else 0.0,
        "malicious_updates": updates,
        "MUR": updates / denominator if denominator else 0.0,
        "mean_before": before.mean,
        "mean_after": after.mean,
        "mean_delta": after.mean - before.mean,
        "sigma_before": before.sigma,
        "sigma_after": after.sigma,
        "sigma_delta": after.sigma - before.sigma,
        "threshold_before": before.threshold,
        "threshold_after": after.threshold,
        "threshold_delta": after.threshold - before.threshold,
        "initial_update_threshold_raw": raw_initial if method == "Guarded EMA" else math.nan,
        "initial_update_threshold_effective": effective_initial if method == "Guarded EMA" else math.nan,
        "initial_gate_width": effective_initial - calibration.tau0 if method == "Guarded EMA" else math.nan,
        "gate_state_count": gate_states if method == "Guarded EMA" else 0,
        "gate_stricter_state_count": gate_strict if method == "Guarded EMA" else 0,
        "gate_stricter_state_fraction": gate_strict / gate_states if gate_states else math.nan,
        "tau_auth_ge_mu_count": tau_ge_mu if method == "Guarded EMA" else 0,
        "tau_auth_ge_mu_fraction": tau_ge_mu / gate_states if gate_states else math.nan,
        "accepted_blocked_by_gate_count": accepted_blocked if method == "Guarded EMA" else 0,
        "accepted_blocked_by_gate_rate": accepted_blocked / denominator if denominator and method == "Guarded EMA" else math.nan,
    }
    return row, profile


def evaluate_guarded_lambda_zero(
    dataset: str,
    enrollment: np.ndarray,
    calibration: Calibration,
    poison_scores: np.ndarray,
    core,
    attack_module,
    mcgill,
) -> bool:
    blind = make_profile(dataset, enrollment, calibration.tau0, core, mcgill)
    guarded = make_profile(dataset, enrollment, calibration.tau0, core, mcgill)
    for raw in poison_scores:
        score = float(raw)
        if score >= blind.threshold:
            update_profile(dataset, blind, score)
        tau = float(guarded.threshold)
        raw_gate = tau  # lambda=0
        if score >= tau and score >= raw_gate:
            update_profile(dataset, guarded, score)
    a = profile_snapshot(dataset, blind, attack_module)
    b = profile_snapshot(dataset, guarded, attack_module)
    return bool(np.allclose([a.mean, a.sigma, a.threshold], [b.mean, b.sigma, b.threshold], atol=1e-14, rtol=0.0))


class ParquetSink:
    def __init__(self, path: Path):
        self.path = path
        self.writer: pq.ParquetWriter | None = None
        self.rows = 0

    def write(self, rows: list[dict[str, object]]) -> None:
        if not rows:
            return
        table = pa.Table.from_pandas(pd.DataFrame(rows), preserve_index=False)
        if self.writer is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.writer = pq.ParquetWriter(
                self.path, table.schema, compression="zstd", compression_level=12,
                use_dictionary=True, write_statistics=True,
            )
        elif table.schema != self.writer.schema:
            table = table.cast(self.writer.schema)
        self.writer.write_table(table, row_group_size=32768)
        self.rows += len(rows)

    def close(self) -> None:
        if self.writer is not None:
            self.writer.close()


class HMOGReferenceAccumulator:
    def __init__(self):
        self.sums: dict[tuple, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.counts: dict[tuple, int] = defaultdict(int)

    def add(self, base: dict[str, object], result: dict[str, object]) -> None:
        key = (base["fold"], base["strategy"], base["K"], result["method"], base["victim"])
        for metric in REFERENCE_METRICS:
            self.sums[key][metric] += float(result[metric])
        self.counts[key] += 1

    def by_fold(self) -> pd.DataFrame:
        rows = []
        for key, totals in self.sums.items():
            fold, strategy, budget, method, victim = key
            count = self.counts[key]
            rows.append({
                "fold": fold, "strategy": strategy, "K": budget,
                "method": method, "victim": victim, "n_paths": count,
                **{metric: totals[metric] / count for metric in REFERENCE_METRICS},
            })
        frame = pd.DataFrame(rows)
        if frame.empty:
            return frame
        grouped = frame.groupby(["fold", "strategy", "K", "method"], as_index=False)
        means = grouped[list(REFERENCE_METRICS)].mean()
        counts = grouped.agg(n_subject_repeat_rows=("n_paths", "sum"), n_subjects=("victim", "nunique"))
        return means.merge(counts, on=["fold", "strategy", "K", "method"])


class McGillReferenceComparator:
    def __init__(self, expected_path: Path):
        expected = pd.read_csv(expected_path)
        expected = expected[expected["method"].isin(METHODS)].copy()
        self.expected = {
            (int(row.victim), int(row.repeat), row.strategy, int(row.K), row.method): row
            for row in expected.itertuples(index=False)
        }
        self.seen: set[tuple] = set()
        self.max_diff: dict[str, float] = defaultdict(float)

    def observe(self, base: dict[str, object], result: dict[str, object]) -> None:
        key = (int(base["victim"]), int(base["repeat"]), str(base["strategy"]), int(base["K"]), str(result["method"]))
        if key not in self.expected:
            raise ProtocolError(f"Unexpected McGill reference path: {key}")
        expected = self.expected[key]
        self.seen.add(key)
        for metric in REFERENCE_METRICS:
            observed = float(result[metric]) * (100.0 if metric in RATE_METRICS else 1.0)
            difference = abs(observed - float(getattr(expected, metric)))
            self.max_diff[metric] = max(self.max_diff[metric], difference)

    def report(self) -> list[dict[str, object]]:
        rows = []
        complete = len(self.seen) == len(self.expected)
        for metric in REFERENCE_METRICS:
            difference = self.max_diff.get(metric, math.inf)
            rows.append({
                "dataset": "McGill", "scope": "path-level authoritative cohort",
                "metric": metric, "expected_rows": len(self.expected),
                "observed_rows": len(self.seen), "max_abs_difference": difference,
                "tolerance": REFERENCE_TOLERANCE,
                "status": "pass" if complete and difference <= REFERENCE_TOLERANCE else "fail",
            })
        return rows


def outcome_base(
    dataset: str, condition: str, fold: int, victim: int, repeat: int,
    strategy: str, budget: int, cohort: str, calibration: Calibration,
    poison_pool: np.ndarray, probe_idx: np.ndarray, genuine_idx: np.ndarray,
    poison_pool_id: str, probe_pool_id: str,
) -> dict[str, object]:
    return {
        "dataset": dataset, "condition": condition,
        "nominal_calibration_far": math.nan if calibration.target is None else calibration.target,
        "fold": fold, "victim": victim, "repeat": repeat,
        "strategy": strategy, "K": budget, "cohort": cohort,
        "n_poisoning_pool": len(poison_pool), "n_impostor_probes": len(probe_idx),
        "n_genuine_probes": len(genuine_idx),
        "poison_pool_id": poison_pool_id, "probe_pool_id": probe_pool_id,
        "tau0": calibration.tau0, "mu0": calibration.mu0,
        "sigma0": calibration.sigma0, "k": calibration.k,
        "k_negative": calibration.k < 0,
    }


def source_rows_for_path(
    base: dict[str, object], method: str, profile: object, dataset: str,
    probe_idx: np.ndarray, probe_subjects: np.ndarray, victim_scores: np.ndarray,
) -> list[dict[str, object]]:
    threshold = float(profile.threshold)
    rows = []
    for source in np.unique(probe_subjects[probe_idx]):
        indices = probe_idx[probe_subjects[probe_idx] == source]
        scores = np.asarray(victim_scores[indices], dtype=np.float64)
        rows.append({
            "dataset": dataset, "condition": base["condition"], "fold": base["fold"],
            "victim": base["victim"], "repeat": base["repeat"],
            "strategy": base["strategy"], "K": base["K"], "method": method,
            "source_id": int(source), "accepted_probe_count": int(np.sum(scores >= threshold)),
            "total_probe_count": int(len(scores)),
        })
    return rows


def run_hmog_conditions(
    project_dir: Path,
    conditions: Sequence[str],
    core,
    attack,
    mcgill,
    outcome_sink: ParquetSink,
    source_sink: ParquetSink,
    calibration_rows: list[dict[str, object]],
    eligibility_rows: list[dict[str, object]],
    reference_accumulator: HMOGReferenceAccumulator | None,
    repeats: int,
    include_primary_sources: bool,
) -> None:
    cache_dir = project_dir / "paper3_cache"
    for fold in range(1, 6):
        data = attack.load_fold(cache_dir, fold, drift=0.0)
        val_scores = np.asarray(data["val_scores"])
        y_val = np.asarray(data["y_val"])
        test_scores = np.asarray(data["test_scores"])
        y_test = np.asarray(data["y_test"])
        sessions = np.asarray(data["session_test"])
        within = np.asarray(data["within_test"])
        calibrations: dict[tuple[int, str], Calibration] = {}
        enrollments: dict[int, np.ndarray] = {}
        for victim in range(test_scores.shape[1]):
            enrollment = np.asarray(val_scores[y_val == victim, victim], dtype=np.float64)
            impostor = np.asarray(val_scores[y_val != victim, victim], dtype=np.float64)
            _, reference = core.eer_from_scores(enrollment, impostor)
            enrollments[victim] = enrollment
            for condition in conditions:
                item = calibration_record(
                    condition, enrollment, impostor, y_val[y_val != victim], reference, 1e-4,
                )
                calibrations[(victim, condition)] = item
                calibration_rows.append(calibration_to_row("HMOG", fold, victim, item))

        rows_buffer: list[dict[str, object]] = []
        source_buffer: list[dict[str, object]] = []
        for victim in range(test_scores.shape[1]):
            genuine_idx = core.chronology_order(sessions, within, np.flatnonzero(y_test == victim))
            impostor_idx = np.flatnonzero(y_test != victim)
            enrollment = enrollments[victim]
            victim_scores = np.asarray(test_scores[:, victim], dtype=np.float64)
            genuine_scores = victim_scores[genuine_idx]
            for repeat in range(repeats):
                split_rng = np.random.default_rng(attack._seed(4242, fold, victim, repeat, stream=0))
                poison_pool, probe_idx = attack.split_impostor_pool(
                    impostor_pool=impostor_idx, y_test=y_test, session_test=sessions,
                    rng=split_rng, probe_fraction=0.5, min_poison_size=MAX_BUDGET,
                )
                assert_disjoint_pools(poison_pool, probe_idx)
                random_rng = np.random.default_rng(attack._seed(4242, fold, victim, repeat, stream=1))
                random_sequence = attack.choose_poison_sequence(
                    "random", poison_pool, victim_scores, 0.0, MAX_BUDGET, random_rng,
                )
                poison_id, probe_id = sha256_indices(poison_pool), sha256_indices(probe_idx)
                for condition in conditions:
                    calibration = calibrations[(victim, condition)]
                    candidate_mask = victim_scores[poison_pool] >= calibration.tau0
                    candidates = poison_pool[candidate_mask]
                    candidate_scores = victim_scores[candidates]
                    order = np.lexsort((candidates, candidate_scores - calibration.tau0))
                    boundary_sequence = candidates[order[:MAX_BUDGET]] if len(candidates) >= MAX_BUDGET else np.empty(0, dtype=np.int64)
                    eligibility_rows.append({
                        "dataset": "HMOG", "fold": fold, "victim": victim, "repeat": repeat,
                        "condition": condition, "nominal_calibration_far": calibration.target,
                        "poison_pool_id": poison_id, "probe_pool_id": probe_id,
                        "n_poisoning_pool": len(poison_pool), "n_probe_samples": len(probe_idx),
                        "n_boundary_candidates": len(candidates),
                        "boundary_K1_feasible": len(candidates) >= 1,
                        "boundary_K2_feasible": len(candidates) >= 2,
                        "boundary_K4_feasible": len(candidates) >= 4,
                        "boundary_K8_feasible": len(candidates) >= 8,
                        "random_K8_feasible": len(poison_pool) >= 8,
                        "infeasible_reason": "" if len(candidates) >= 8 else f"only_{len(candidates)}_accepted_boundary_candidates",
                    })
                    sequences = [("random", random_sequence, "all_path_random")]
                    if len(candidates) >= 8:
                        sequences.append(("boundary", boundary_sequence, "boundary_k8_feasible"))
                    for strategy, sequence, cohort in sequences:
                        for budget in BUDGETS:
                            base = outcome_base(
                                "HMOG", condition, fold, victim, repeat, strategy, budget,
                                cohort, calibration, poison_pool, probe_idx, genuine_idx,
                                poison_id, probe_id,
                            )
                            prefix = sequence[:budget]
                            poison_scores = victim_scores[prefix]
                            for method in METHODS:
                                result, profile = evaluate_method(
                                    "HMOG", method, enrollment, calibration, poison_scores,
                                    victim_scores[probe_idx], genuine_scores, core, attack, mcgill,
                                )
                                rows_buffer.append({**base, **result})
                                if reference_accumulator is not None and condition == "reference" and len(candidates) >= 8:
                                    reference_accumulator.add(base, result)
                                if (
                                    include_primary_sources and condition == "far_1pct"
                                    and strategy == "boundary" and budget == 8
                                ):
                                    additions = source_rows_for_path(
                                        base, method, profile, "HMOG", probe_idx, y_test, victim_scores,
                                    )
                                    accepted = sum(int(item["accepted_probe_count"]) for item in additions)
                                    total = sum(int(item["total_probe_count"]) for item in additions)
                                    if total != len(probe_idx) or not np.isclose(accepted / total, result["post_ASR"]):
                                        raise ProtocolError("Source-specific HMOG counts do not reproduce path ASR")
                                    source_buffer.extend(additions)
                            if budget == MAX_BUDGET and not evaluate_guarded_lambda_zero(
                                "HMOG", enrollment, calibration, poison_scores, core, attack, mcgill,
                            ):
                                raise ProtocolError("Guarded lambda=0 does not reproduce Blind on HMOG")
                    if len(rows_buffer) >= 25000:
                        outcome_sink.write(rows_buffer)
                        rows_buffer.clear()
                    if len(source_buffer) >= 25000:
                        source_sink.write(source_buffer)
                        source_buffer.clear()
        outcome_sink.write(rows_buffer)
        source_sink.write(source_buffer)
        print(f"HMOG fold {fold}/5 complete for {','.join(conditions)}", flush=True)


def run_mcgill_conditions(
    cache_path: Path,
    conditions: Sequence[str],
    core,
    attack,
    mcgill,
    outcome_sink: ParquetSink,
    calibration_rows: list[dict[str, object]],
    eligibility_rows: list[dict[str, object]],
    reference_comparator: McGillReferenceComparator | None,
    repeats: int,
) -> None:
    with np.load(cache_path) as archive:
        cache = {name: np.asarray(archive[name]) for name in archive.files}
    enroll_scores = cache["enroll_scores"]
    enroll_subjects = cache["enroll_subjects"]
    day2_scores = cache["day2_scores"]
    day2_subjects = cache["day2_subjects"]
    day2_within = cache["day2_within"]
    calibrations: dict[tuple[int, str], Calibration] = {}
    enrollments: dict[int, np.ndarray] = {}
    for victim in range(1, 21):
        enrollment = np.asarray(enroll_scores[enroll_subjects == victim, victim - 1], dtype=np.float64)
        impostor = np.asarray(enroll_scores[enroll_subjects != victim, victim - 1], dtype=np.float64)
        reference = mcgill.calibrate_threshold(enrollment, impostor)
        enrollments[victim] = enrollment
        for condition in conditions:
            item = calibration_record(
                condition, enrollment, impostor, enroll_subjects[enroll_subjects != victim], reference, 1e-4,
            )
            calibrations[(victim, condition)] = item
            calibration_rows.append(calibration_to_row("McGill", -1, victim, item))

    rows_buffer: list[dict[str, object]] = []
    for victim in range(1, 21):
        enrollment = enrollments[victim]
        victim_scores = np.asarray(day2_scores[:, victim - 1], dtype=np.float64)
        genuine_idx = np.flatnonzero(day2_subjects == victim)
        genuine_scores = victim_scores[genuine_idx]
        sources = [sid for sid in range(1, 21) if sid != victim]
        for repeat in range(repeats):
            split_rng = np.random.default_rng(np.random.SeedSequence([4242, victim, repeat, 0]))
            poison_sources, probe_sources = mcgill.split_source_identities(sources, split_rng, 0.5)
            poison_pool = mcgill.source_temporal_pool(day2_subjects, day2_within, poison_sources, half="first")
            probe_idx = mcgill.source_temporal_pool(day2_subjects, day2_within, probe_sources, half="second")
            assert_disjoint_pools(poison_pool, probe_idx)
            random_rng = np.random.default_rng(np.random.SeedSequence([4242, victim, repeat, 1]))
            random_sequence = mcgill.choose_poison_sequence(
                "random", poison_pool, victim_scores, 0.0, MAX_BUDGET, random_rng,
            )
            poison_id, probe_id = sha256_indices(poison_pool), sha256_indices(probe_idx)
            for condition in conditions:
                calibration = calibrations[(victim, condition)]
                candidate_mask = victim_scores[poison_pool] >= calibration.tau0
                candidates = poison_pool[candidate_mask]
                candidate_scores = victim_scores[candidates]
                order = np.lexsort((candidates, candidate_scores - calibration.tau0))
                boundary_sequence = candidates[order[:MAX_BUDGET]] if len(candidates) >= MAX_BUDGET else np.empty(0, dtype=np.int64)
                eligibility_rows.append({
                    "dataset": "McGill", "fold": -1, "victim": victim, "repeat": repeat,
                    "condition": condition, "nominal_calibration_far": calibration.target,
                    "poison_pool_id": poison_id, "probe_pool_id": probe_id,
                    "n_poisoning_pool": len(poison_pool), "n_probe_samples": len(probe_idx),
                    "n_boundary_candidates": len(candidates),
                    "boundary_K1_feasible": len(candidates) >= 1,
                    "boundary_K2_feasible": len(candidates) >= 2,
                    "boundary_K4_feasible": len(candidates) >= 4,
                    "boundary_K8_feasible": len(candidates) >= 8,
                    "random_K8_feasible": len(poison_pool) >= 8,
                    "infeasible_reason": "" if len(candidates) >= 8 else f"only_{len(candidates)}_accepted_boundary_candidates",
                })
                sequences = [("random", random_sequence, "all_path_random")]
                if len(candidates) >= 8:
                    sequences.append(("boundary", boundary_sequence, "boundary_k8_feasible"))
                for strategy, sequence, cohort in sequences:
                    for budget in BUDGETS:
                        base = outcome_base(
                            "McGill", condition, -1, victim, repeat, strategy, budget,
                            cohort, calibration, poison_pool, probe_idx, genuine_idx,
                            poison_id, probe_id,
                        )
                        poison_scores = victim_scores[sequence[:budget]]
                        for method in METHODS:
                            result, _ = evaluate_method(
                                "McGill", method, enrollment, calibration, poison_scores,
                                victim_scores[probe_idx], genuine_scores, core, attack, mcgill,
                            )
                            rows_buffer.append({**base, **result})
                            if reference_comparator is not None and condition == "reference":
                                reference_comparator.observe(base, result)
                        if budget == MAX_BUDGET and not evaluate_guarded_lambda_zero(
                            "McGill", enrollment, calibration, poison_scores, core, attack, mcgill,
                        ):
                            raise ProtocolError("Guarded lambda=0 does not reproduce Blind on McGill")
                if len(rows_buffer) >= 25000:
                    outcome_sink.write(rows_buffer)
                    rows_buffer.clear()
    outcome_sink.write(rows_buffer)
    print(f"McGill complete for {','.join(conditions)}", flush=True)


def compare_hmog_reference(actual: pd.DataFrame, expected_path: Path) -> list[dict[str, object]]:
    expected = pd.read_csv(expected_path)
    selected = expected[
        (expected["method"].isin(("Frozen", "Blind EMA")))
        | ((expected["method"] == "Guarded EMA") & np.isclose(expected["lambda_value"], 0.25))
    ].copy()
    selected = selected[["fold", "strategy", "K", "method", "n_subject_repeat_rows", "n_subjects", *REFERENCE_METRICS]]
    merged = selected.merge(actual, on=["fold", "strategy", "K", "method"], suffixes=("_expected", "_observed"), how="outer", indicator=True)
    rows = []
    keys_complete = bool((merged["_merge"] == "both").all())
    for metric in REFERENCE_METRICS:
        scale = 100.0 if metric in RATE_METRICS else 1.0
        differences = np.abs(merged[f"{metric}_expected"] - scale * merged[f"{metric}_observed"])
        maximum = float(differences.max()) if len(differences) and np.all(np.isfinite(differences)) else math.inf
        rows.append({
            "dataset": "HMOG", "scope": "fold-level legacy common-boundary-feasible cohort",
            "metric": metric, "expected_rows": len(selected), "observed_rows": len(actual),
            "max_abs_difference": maximum, "tolerance": REFERENCE_TOLERANCE,
            "status": "pass" if keys_complete and maximum <= REFERENCE_TOLERANCE else "fail",
        })
    count_diff = max(
        float(np.nanmax(np.abs(merged["n_subject_repeat_rows_expected"] - merged["n_subject_repeat_rows_observed"]))),
        float(np.nanmax(np.abs(merged["n_subjects_expected"] - merged["n_subjects_observed"]))),
    )
    rows.append({
        "dataset": "HMOG", "scope": "fold-level legacy common-boundary-feasible cohort",
        "metric": "path_and_subject_counts", "expected_rows": len(selected), "observed_rows": len(actual),
        "max_abs_difference": count_diff, "tolerance": 0.0,
        "status": "pass" if keys_complete and count_diff == 0 else "fail",
    })
    return rows


def summarize_eligibility(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (dataset, condition), group in frame.groupby(["dataset", "condition"], sort=True):
        for budget in (1, 2, 4, 8):
            mask = group[f"boundary_K{budget}_feasible"].astype(bool)
            eligible = group[mask]
            rows.append({
                "dataset": dataset, "condition": condition,
                "nominal_calibration_far": TARGETS[condition], "strategy": "boundary", "K": budget,
                "total_planned_paths": len(group), "eligible_paths": len(eligible),
                "eligible_path_fraction": len(eligible) / len(group) if len(group) else math.nan,
                "unique_eligible_victims": int(eligible["victim"].nunique()),
                "eligible_victim_fold_pairs": int(eligible[["victim", "fold"]].drop_duplicates().shape[0]),
                "candidate_min": int(group["n_boundary_candidates"].min()),
                "candidate_q25": float(group["n_boundary_candidates"].quantile(0.25)),
                "candidate_median": float(group["n_boundary_candidates"].median()),
                "candidate_q75": float(group["n_boundary_candidates"].quantile(0.75)),
                "candidate_max": int(group["n_boundary_candidates"].max()),
            })
        rows.append({
            "dataset": dataset, "condition": condition,
            "nominal_calibration_far": TARGETS[condition], "strategy": "random", "K": 8,
            "total_planned_paths": len(group), "eligible_paths": int(group["random_K8_feasible"].sum()),
            "eligible_path_fraction": float(group["random_K8_feasible"].mean()),
            "unique_eligible_victims": int(group.loc[group["random_K8_feasible"], "victim"].nunique()),
            "eligible_victim_fold_pairs": int(group.loc[group["random_K8_feasible"], ["victim", "fold"]].drop_duplicates().shape[0]),
            "candidate_min": math.nan, "candidate_q25": math.nan, "candidate_median": math.nan,
            "candidate_q75": math.nan, "candidate_max": math.nan,
        })
    return pd.DataFrame(rows)


def assert_partition_invariance(frame: pd.DataFrame) -> None:
    keys = ["dataset", "fold", "victim", "repeat"]
    grouped = frame.groupby(keys, sort=False).agg(
        conditions=("condition", "nunique"),
        poison_ids=("poison_pool_id", "nunique"),
        probe_ids=("probe_pool_id", "nunique"),
        poison_sizes=("n_poisoning_pool", "nunique"),
        probe_sizes=("n_probe_samples", "nunique"),
    )
    expected = frame["condition"].nunique()
    invalid = grouped[
        (grouped["conditions"] != expected) | (grouped["poison_ids"] != 1)
        | (grouped["probe_ids"] != 1) | (grouped["poison_sizes"] != 1)
        | (grouped["probe_sizes"] != 1)
    ]
    if not invalid.empty:
        raise ProtocolError("Pool partitions are not invariant across operating points")


def victim_level(outcomes: pd.DataFrame) -> pd.DataFrame:
    keys = ["dataset", "condition", "strategy", "K", "method", "victim"]
    metrics = [metric for metric in SUMMARY_METRICS if metric in outcomes]
    hmog = outcomes[outcomes["dataset"] == "HMOG"]
    mcgill = outcomes[outcomes["dataset"] == "McGill"]
    pieces = []
    if not hmog.empty:
        fold_keys = keys + ["fold"]
        per_fold = hmog.groupby(fold_keys, as_index=False)[metrics].mean()
        values = per_fold.groupby(keys, as_index=False)[metrics].mean()
        counts = per_fold.groupby(keys, as_index=False).agg(n_contributing_folds=("fold", "nunique"))
        paths = hmog.groupby(keys, as_index=False).agg(n_paths=("repeat", "size"))
        pieces.append(values.merge(counts, on=keys).merge(paths, on=keys))
    if not mcgill.empty:
        values = mcgill.groupby(keys, as_index=False)[metrics].mean()
        paths = mcgill.groupby(keys, as_index=False).agg(n_paths=("repeat", "size"))
        values["n_contributing_folds"] = 1
        pieces.append(values.merge(paths, on=keys))
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def bootstrap_mean(values: np.ndarray, draws: int, seed: int) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=np.float64)
    if not len(array):
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(seed)
    estimates = np.empty(draws, dtype=np.float64)
    for start in range(0, draws, 1000):
        count = min(1000, draws - start)
        indices = rng.integers(0, len(array), size=(count, len(array)))
        estimates[start:start + count] = array[indices].mean(axis=1)
    return float(array.mean()), float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))


def make_summaries(victims: pd.DataFrame, draws: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    absolute_rows = []
    effect_subject_rows = []
    effect_bootstrap_rows = []
    group_keys = ["dataset", "condition", "strategy", "K"]
    for group_key, group in victims.groupby(group_keys, sort=True):
        identity = dict(zip(group_keys, group_key))
        for method in METHODS:
            selected = group[group["method"] == method]
            for metric in SUMMARY_METRICS:
                values = selected[metric].dropna().to_numpy(dtype=float)
                mean, low, high = bootstrap_mean(values, draws, stable_seed(seed, "absolute", *group_key, method, metric))
                scale = 100.0 if metric in RATE_METRICS else 1.0
                absolute_rows.append({
                    **identity, "nominal_calibration_far": TARGETS[identity["condition"]],
                    "method": method, "metric": metric, "n_victims": len(values),
                    "mean": mean * scale, "ci_low": low * scale, "ci_high": high * scale,
                    "unit": "percent" if scale == 100.0 else "score_or_count",
                    "inference_status": "not_estimable" if not len(values) else ("sparse_descriptive" if len(values) < 10 else "estimable"),
                })
        for metric in SUMMARY_METRICS:
            pivot = group.pivot_table(index="victim", columns="method", values=metric, aggfunc="mean")
            for method_a, method_b, label in (
                ("Blind EMA", "Frozen", "Blind EMA minus Frozen"),
                ("Guarded EMA", "Blind EMA", "Guarded EMA minus Blind EMA"),
                ("Guarded EMA", "Frozen", "Guarded EMA minus Frozen"),
            ):
                if method_a not in pivot or method_b not in pivot:
                    effects = pd.Series(dtype=float)
                else:
                    effects = (pivot[method_a] - pivot[method_b]).dropna()
                scale = 100.0 if metric in RATE_METRICS else 1.0
                for victim, value in effects.items():
                    source = group[group["victim"] == victim]
                    effect_subject_rows.append({
                        **identity, "nominal_calibration_far": TARGETS[identity["condition"]],
                        "contrast": label, "metric": metric, "victim": victim,
                        "effect": float(value) * scale,
                        "n_contributing_folds": int(source["n_contributing_folds"].max()),
                        "n_paths": int(source[source["method"] == method_a]["n_paths"].max()),
                    })
                mean, low, high = bootstrap_mean(
                    effects.to_numpy(dtype=float), draws,
                    stable_seed(seed, "effect", *group_key, label, metric),
                )
                effect_bootstrap_rows.append({
                    **identity, "nominal_calibration_far": TARGETS[identity["condition"]],
                    "contrast": label, "method_a": method_a, "method_b": method_b,
                    "metric": metric, "n_victims": len(effects),
                    "mean_effect": mean * scale, "ci_low": low * scale, "ci_high": high * scale,
                    "unit": "percentage_points" if scale == 100.0 else "score_or_count_difference",
                    "inference_status": "not_estimable" if not len(effects) else ("sparse_descriptive" if len(effects) < 10 else "estimable"),
                })
    return pd.DataFrame(absolute_rows), pd.DataFrame(effect_subject_rows), pd.DataFrame(effect_bootstrap_rows)


def complete_summary_grid(
    operating: pd.DataFrame, effects: pd.DataFrame, eligibility: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Represent non-estimable zero-feasibility cells explicitly as NA rows."""
    absolute_rows = []
    effect_rows = []
    contrasts = (
        ("Blind EMA minus Frozen", "Blind EMA", "Frozen"),
        ("Guarded EMA minus Blind EMA", "Guarded EMA", "Blind EMA"),
        ("Guarded EMA minus Frozen", "Guarded EMA", "Frozen"),
    )
    for item in eligibility.itertuples(index=False):
        if item.strategy == "random":
            budgets = BUDGETS
        elif item.K == 8:
            budgets = BUDGETS
        else:
            continue
        for budget in budgets:
            key = (
                (operating["dataset"] == item.dataset)
                & (operating["condition"] == item.condition)
                & (operating["strategy"] == item.strategy)
                & (operating["K"] == budget)
            )
            if not key.any():
                for method in METHODS:
                    for metric in SUMMARY_METRICS:
                        absolute_rows.append({
                            "dataset": item.dataset, "condition": item.condition,
                            "strategy": item.strategy, "K": budget,
                            "nominal_calibration_far": TARGETS[item.condition],
                            "method": method, "metric": metric, "n_victims": 0,
                            "mean": math.nan, "ci_low": math.nan, "ci_high": math.nan,
                            "unit": "percent" if metric in RATE_METRICS else "score_or_count",
                            "inference_status": "not_estimable_zero_feasibility",
                        })
            for label, method_a, method_b in contrasts:
                for metric in SUMMARY_METRICS:
                    effect_key = (
                        (effects["dataset"] == item.dataset)
                        & (effects["condition"] == item.condition)
                        & (effects["strategy"] == item.strategy)
                        & (effects["K"] == budget)
                        & (effects["contrast"] == label)
                        & (effects["metric"] == metric)
                    )
                    if not effect_key.any():
                        effect_rows.append({
                            "dataset": item.dataset, "condition": item.condition,
                            "strategy": item.strategy, "K": budget,
                            "nominal_calibration_far": TARGETS[item.condition],
                            "contrast": label, "method_a": method_a, "method_b": method_b,
                            "metric": metric, "n_victims": 0,
                            "mean_effect": math.nan, "ci_low": math.nan, "ci_high": math.nan,
                            "unit": "percentage_points" if metric in RATE_METRICS else "score_or_count_difference",
                            "inference_status": "not_estimable_zero_feasibility",
                        })
    if absolute_rows:
        operating = pd.concat([operating, pd.DataFrame(absolute_rows)], ignore_index=True)
    if effect_rows:
        effects = pd.concat([effects, pd.DataFrame(effect_rows)], ignore_index=True)
    operating = operating.drop_duplicates(["dataset", "condition", "strategy", "K", "method", "metric"])
    effects = effects.drop_duplicates(["dataset", "condition", "strategy", "K", "contrast", "metric"])
    return operating, effects


def make_gate_diagnostics(outcomes: pd.DataFrame, calibration: pd.DataFrame) -> pd.DataFrame:
    rows = []
    guarded = outcomes[outcomes["method"] == "Guarded EMA"]
    for (dataset, condition, strategy, budget), group in guarded.groupby(["dataset", "condition", "strategy", "K"], sort=True):
        states = int(group["gate_state_count"].sum())
        rows.append({
            "dataset": dataset, "condition": condition, "nominal_calibration_far": TARGETS[condition],
            "strategy": strategy, "K": budget, "n_paths": len(group),
            "initial_gate_width_mean": float(group["initial_gate_width"].mean()),
            "gate_states": states,
            "gate_stricter_states": int(group["gate_stricter_state_count"].sum()),
            "gate_stricter_state_fraction": float(group["gate_stricter_state_count"].sum() / states) if states else math.nan,
            "tau_auth_ge_mu_states": int(group["tau_auth_ge_mu_count"].sum()),
            "tau_auth_ge_mu_fraction": float(group["tau_auth_ge_mu_count"].sum() / states) if states else math.nan,
            "accepted_blocked_by_gate_count": int(group["accepted_blocked_by_gate_count"].sum()),
            "accepted_blocked_by_gate_rate": float(group["accepted_blocked_by_gate_count"].sum() / (len(group) * budget)) if budget else math.nan,
            "mean_MUR": float(group["MUR"].mean()),
            "mean_threshold_delta": float(group["threshold_delta"].mean()),
        })
    result = pd.DataFrame(rows)
    init = calibration.groupby(["dataset", "condition"], as_index=False).agg(
        n_claimant_folds=("victim", "size"),
        negative_k_fraction=("k", lambda x: float(np.mean(np.asarray(x) < 0))),
        initial_tau_ge_mu_fraction=("initial_tau_ge_mu", "mean"),
    )
    return result.merge(init, on=["dataset", "condition"], how="left")


def two_way_bootstrap(source_path: Path, draws: int, seed: int) -> pd.DataFrame:
    if not source_path.is_file():
        return pd.DataFrame([{
            "dataset": "HMOG", "condition": "far_1pct", "strategy": "boundary", "K": 8,
            "contrast": "not available", "n_victims": 0, "n_paths": 0,
            "draws_requested": draws, "draws_valid": 0, "mean_effect": math.nan,
            "ci_low": math.nan, "ci_high": math.nan, "status": "not_estimable_no_primary_source_records",
        }])
    source = pd.read_parquet(source_path)
    if source.empty:
        return pd.DataFrame()
    path_cols = ["fold", "victim", "repeat"]
    path_index = source[path_cols].drop_duplicates().sort_values(path_cols).reset_index(drop=True)
    path_index["path_row"] = np.arange(len(path_index))
    source = source.merge(path_index, on=path_cols)
    sources = np.sort(source["source_id"].unique())
    source_map = {value: index for index, value in enumerate(sources)}
    matrices: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for method in METHODS:
        selected = source[source["method"] == method]
        accepted = np.zeros((len(path_index), len(sources)), dtype=np.float32)
        total = np.zeros_like(accepted)
        rows = selected["path_row"].to_numpy(dtype=int)
        cols = selected["source_id"].map(source_map).to_numpy(dtype=int)
        accepted[rows, cols] = selected["accepted_probe_count"].to_numpy(dtype=np.float32)
        total[rows, cols] = selected["total_probe_count"].to_numpy(dtype=np.float32)
        matrices[method] = (accepted, total)
    victims = np.sort(path_index["victim"].unique())
    victim_map = {value: index for index, value in enumerate(victims)}
    path_weights = np.zeros((len(victims), len(path_index)), dtype=np.float64)
    for victim in victims:
        vrows = path_index[path_index["victim"] == victim]
        folds = np.sort(vrows["fold"].unique())
        for fold in folds:
            indices = vrows.loc[vrows["fold"] == fold, "path_row"].to_numpy(dtype=int)
            path_weights[victim_map[victim], indices] = 1.0 / (len(folds) * len(indices))
    rng = np.random.default_rng(seed)
    estimates = {
        "Blind EMA minus Frozen": np.empty(draws, dtype=np.float64),
        "Guarded EMA minus Blind EMA": np.empty(draws, dtype=np.float64),
        "Guarded EMA minus Frozen": np.empty(draws, dtype=np.float64),
    }
    batch_size = 100
    valid = np.ones(draws, dtype=bool)
    for start in range(0, draws, batch_size):
        count = min(batch_size, draws - start)
        source_draws = rng.integers(0, len(sources), size=(count, len(sources)))
        source_weights = np.zeros((len(sources), count), dtype=np.float32)
        for column in range(count):
            source_weights[:, column] = np.bincount(source_draws[column], minlength=len(sources))
        rates: dict[str, np.ndarray] = {}
        for method, (accepted, total) in matrices.items():
            numerator = accepted @ source_weights
            denominator = total @ source_weights
            if np.any(denominator == 0):
                raise ProtocolError("Two-way bootstrap produced a zero path denominator")
            rates[method] = numerator / denominator
        victim_draws = rng.integers(0, len(victims), size=(count, len(victims)))
        victim_weights = np.zeros((len(victims), count), dtype=np.float64)
        for column in range(count):
            victim_weights[:, column] = np.bincount(victim_draws[column], minlength=len(victims))
        for label, a, b in (
            ("Blind EMA minus Frozen", "Blind EMA", "Frozen"),
            ("Guarded EMA minus Blind EMA", "Guarded EMA", "Blind EMA"),
            ("Guarded EMA minus Frozen", "Guarded EMA", "Frozen"),
        ):
            per_victim = path_weights @ (rates[a] - rates[b])
            values = np.sum(per_victim * victim_weights, axis=0) / np.sum(victim_weights, axis=0)
            estimates[label][start:start + count] = values
    rows = []
    original_rates = {}
    ones = np.ones(len(sources), dtype=np.float32)
    for method, (accepted, total) in matrices.items():
        original_rates[method] = (accepted @ ones) / (total @ ones)
    for label, values in estimates.items():
        values = values[valid]
        method_a, method_b = {
            "Blind EMA minus Frozen": ("Blind EMA", "Frozen"),
            "Guarded EMA minus Blind EMA": ("Guarded EMA", "Blind EMA"),
            "Guarded EMA minus Frozen": ("Guarded EMA", "Frozen"),
        }[label]
        observed_per_victim = path_weights @ (original_rates[method_a] - original_rates[method_b])
        rows.append({
            "dataset": "HMOG", "condition": "far_1pct", "strategy": "boundary", "K": 8,
            "contrast": label, "n_victims": len(victims), "n_paths": len(path_index),
            "n_sources": len(sources), "draws_requested": draws, "draws_valid": len(values),
            "mean_effect": float(observed_per_victim.mean() * 100.0),
            "ci_low": float(np.quantile(values, 0.025) * 100.0),
            "ci_high": float(np.quantile(values, 0.975) * 100.0),
            "status": "complete_product_weight_victim_source_bootstrap",
        })
    return pd.DataFrame(rows)


def make_figures(
    output_dir: Path, calibration: pd.DataFrame, eligibility_summary: pd.DataFrame,
    operating_summary: pd.DataFrame, effects: pd.DataFrame, gate: pd.DataFrame,
) -> list[str]:
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(exist_ok=True)
    created = []
    order = ["reference", "far_5pct", "far_1pct"]
    labels = ["Reference", "Nominal 5%", "Nominal 1%"]
    colors = {"HMOG": "#2459a9", "McGill": "#cb5a36"}

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    for dataset in ("HMOG", "McGill"):
        cal = calibration[calibration["dataset"] == dataset].groupby("condition")["achieved_calibration_far"].mean().reindex(order) * 100
        held = operating_summary[
            (operating_summary["dataset"] == dataset) & (operating_summary["strategy"] == "random")
            & (operating_summary["K"] == 0) & (operating_summary["method"] == "Frozen")
            & (operating_summary["metric"] == "post_ASR")
        ].set_index("condition")["mean"].reindex(order)
        axes[0].plot(labels, cal, marker="o", color=colors[dataset], label=dataset)
        axes[1].plot(labels, held, marker="o", color=colors[dataset], label=dataset)
    axes[0].set_title("Achieved calibration FAR")
    axes[1].set_title("Observed held-out Frozen FAR")
    for axis in axes:
        axis.set_ylabel("FAR (%)")
        axis.grid(alpha=0.25)
        axis.legend(frameon=False)
    for suffix in ("png", "pdf"):
        path = figure_dir / f"calibration_vs_heldout_far.{suffix}"
        fig.savefig(path, dpi=220)
        created.append(str(path.relative_to(output_dir)))
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True, sharey=True)
    for axis, dataset in zip(axes, ("HMOG", "McGill")):
        selected = effects[
            (effects["dataset"] == dataset) & (effects["strategy"] == "boundary")
            & (effects["K"] == 8) & (effects["metric"] == "post_ASR")
            & effects["contrast"].isin(("Blind EMA minus Frozen", "Guarded EMA minus Blind EMA"))
        ]
        for offset, (contrast, marker) in enumerate((("Blind EMA minus Frozen", "o"), ("Guarded EMA minus Blind EMA", "s"))):
            part = selected[selected["contrast"] == contrast].set_index("condition").reindex(order)
            x = np.arange(3) + (offset - 0.5) * 0.12
            y = part["mean_effect"].to_numpy(dtype=float)
            low = part["ci_low"].to_numpy(dtype=float)
            high = part["ci_high"].to_numpy(dtype=float)
            # Operating points can have different boundary-feasible cohorts;
            # separate markers avoid implying a paired cross-target trajectory.
            axis.errorbar(
                x, y, yerr=np.vstack([y - low, high - y]), marker=marker,
                linestyle="none", capsize=3, label=contrast,
            )
        axis.axhline(0, color="black", linewidth=0.8)
        axis.set_xticks(np.arange(3), labels)
        axis.set_title(dataset)
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Paired ASR effect (percentage points)")
    axes[1].legend(frameon=False, fontsize=8)
    for suffix in ("png", "pdf"):
        path = figure_dir / f"boundary_k8_effects.{suffix}"
        fig.savefig(path, dpi=220)
        created.append(str(path.relative_to(output_dir)))
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True, sharey=True)
    for axis, dataset in zip(axes, ("HMOG", "McGill")):
        selected = eligibility_summary[
            (eligibility_summary["dataset"] == dataset) & (eligibility_summary["strategy"] == "boundary")
        ]
        for condition, label in zip(order, labels):
            part = selected[selected["condition"] == condition].sort_values("K")
            axis.plot(part["K"], 100 * part["eligible_path_fraction"], marker="o", label=label)
        axis.set_title(dataset)
        axis.set_xlabel("Presented poisoning budget K")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Feasible planned paths (%)")
    axes[1].legend(frameon=False)
    for suffix in ("png", "pdf"):
        path = figure_dir / f"boundary_feasibility.{suffix}"
        fig.savefig(path, dpi=220)
        created.append(str(path.relative_to(output_dir)))
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    selected = gate[(gate["strategy"] == "boundary") & (gate["K"] == 8)]
    for dataset in ("HMOG", "McGill"):
        part = selected[selected["dataset"] == dataset].set_index("condition").reindex(order)
        axes[0].plot(labels, 100 * part["gate_stricter_state_fraction"], marker="o", label=dataset)
        axes[1].plot(labels, 100 * part["tau_auth_ge_mu_fraction"], marker="o", label=dataset)
    axes[0].set_title("Guarded gate stricter than authentication")
    axes[1].set_title(r"States with $\tau_{auth} \geq \mu_{enroll}$")
    for axis in axes:
        axis.set_ylabel("Poisoning states (%)")
        axis.grid(alpha=0.25)
        axis.legend(frameon=False)
    for suffix in ("png", "pdf"):
        path = figure_dir / f"guarded_gate_diagnostics.{suffix}"
        fig.savefig(path, dpi=220)
        created.append(str(path.relative_to(output_dir)))
    plt.close(fig)
    return created


def pct(value: float) -> str:
    return "NA" if pd.isna(value) else f"{value:.2f}%"


def make_report(
    output_dir: Path, reference: pd.DataFrame, calibration: pd.DataFrame,
    eligibility: pd.DataFrame, summary: pd.DataFrame, effects: pd.DataFrame,
    gate: pd.DataFrame, two_way: pd.DataFrame, mode: str,
) -> None:
    passed = bool((reference["status"] == "pass").all())
    lines = [
        "# Operating-point sensitivity report", "",
        f"Status: **{'complete' if mode == 'full' else 'reference check complete'}**.", "",
        f"Reference reproduction: **{'PASS' if passed else 'FAIL'}**.", "",
    ]
    if mode != "full":
        lines += ["No 5%/1% sensitivity outcome was computed in this reference-only run.", ""]
        (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    lines += [
        "The nominal targets are calibration constraints, not observed held-out FAR guarantees.", "",
        "## Held-out Frozen operating points", "",
        "| Dataset | Condition | Calibration FAR | Held-out FAR | FRR | HTER |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for dataset in ("HMOG", "McGill"):
        for condition in CONDITIONS:
            cal = calibration[(calibration.dataset == dataset) & (calibration.condition == condition)]["achieved_calibration_far"].mean() * 100
            values = summary[(summary.dataset == dataset) & (summary.condition == condition) & (summary.strategy == "random") & (summary.K == 0) & (summary.method == "Frozen")].set_index("metric")
            lines.append(
                f"| {dataset} | {condition} | {pct(cal)} | {pct(values.loc['post_ASR','mean'])} | "
                f"{pct(values.loc['post_FRR','mean'])} | {pct(values.loc['HTER','mean'])} |"
            )
    lines += ["", "## Boundary K=8 effects", "", "| Dataset | Condition | Eligible paths | Victims | Contrast | Effect [95% CI], pp |", "|---|---:|---:|---:|---|---:|"]
    for dataset in ("HMOG", "McGill"):
        for condition in CONDITIONS:
            elig = eligibility[(eligibility.dataset == dataset) & (eligibility.condition == condition) & (eligibility.strategy == "boundary") & (eligibility.K == 8)].iloc[0]
            for contrast in ("Blind EMA minus Frozen", "Guarded EMA minus Blind EMA"):
                row = effects[(effects.dataset == dataset) & (effects.condition == condition) & (effects.strategy == "boundary") & (effects.K == 8) & (effects.metric == "post_ASR") & (effects.contrast == contrast)].iloc[0]
                estimate = "NA" if pd.isna(row.mean_effect) else f"{row.mean_effect:+.2f} [{row.ci_low:+.2f}, {row.ci_high:+.2f}]"
                lines.append(f"| {dataset} | {condition} | {int(elig.eligible_paths)} | {int(elig.unique_eligible_victims)} | {contrast} | {estimate} |")
    lines += ["", "## Interpretation guardrails", "", "- Boundary estimates are conditional on operating-point-specific K=8 feasibility.", "- Cross-target effects can involve different paths and must not be read as strictly paired target comparisons.", "- The victim bootstrap conditions on fixed trained models and observed probe pools.", "- The victim×source analysis is secondary and does not remove classifier-training or population uncertainty.", ""]
    if not two_way.empty:
        lines += ["## Primary victim×source sensitivity", ""]
        for row in two_way.itertuples():
            lines.append(f"- {row.contrast}: {row.mean_effect:+.2f} pp, 95% CI [{row.ci_low:+.2f}, {row.ci_high:+.2f}] ({row.status})." if pd.notna(row.mean_effect) else f"- {row.contrast}: not estimable ({row.status}).")
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def output_hashes(output_dir: Path) -> dict[str, dict[str, object]]:
    hashes = {}
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            hashes[str(path.relative_to(output_dir))] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    return hashes


def run(args: argparse.Namespace) -> Path:
    project_dir = Path(args.project_dir).resolve()
    protocol_path = project_dir / "experiments" / "paper3_operating_point_sensitivity.json"
    mcgill_cache = Path(args.mcgill_cache).resolve()
    output_dir = Path(args.output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_hash = sha256_file(protocol_path)
    cache_hashes = verify_protocol_and_inputs(project_dir, protocol_path, mcgill_cache)
    core, attack, mcgill = load_modules(project_dir)
    outcomes_sink = ParquetSink(output_dir / "outcomes_by_path.parquet")
    source_sink = ParquetSink(output_dir / "probe_outcomes_by_source.parquet")
    calibration_rows: list[dict[str, object]] = []
    eligibility_rows: list[dict[str, object]] = []
    reference_accumulator = HMOGReferenceAccumulator()
    mcgill_comparator = McGillReferenceComparator(
        project_dir / "results" / "paper3_external_mcgill_20261003_v1" / "attack_subject_repeat.csv"
    )
    status = "running"
    error = None
    reference_rows: list[dict[str, object]] = []
    figures: list[str] = []
    try:
        # Mandatory reference gate.  No sensitivity target is evaluated before it passes.
        run_hmog_conditions(
            project_dir, ("reference",), core, attack, mcgill, outcomes_sink, source_sink,
            calibration_rows, eligibility_rows, reference_accumulator, args.repeats, False,
        )
        run_mcgill_conditions(
            mcgill_cache, ("reference",), core, attack, mcgill, outcomes_sink,
            calibration_rows, eligibility_rows, mcgill_comparator, args.repeats,
        )
        reference_rows.extend(compare_hmog_reference(
            reference_accumulator.by_fold(),
            project_dir / "results" / "paper3_guarded_20260930" / "paper3_guarded_by_fold.csv",
        ))
        reference_rows.extend(mcgill_comparator.report())
        reference_frame = pd.DataFrame(reference_rows)
        reference_frame.to_csv(output_dir / "reference_reproduction.csv", index=False)
        if not bool((reference_frame["status"] == "pass").all()):
            raise ProtocolError("Reference reproduction failed; sensitivity targets were not evaluated")

        if args.mode == "full":
            run_hmog_conditions(
                project_dir, ("far_5pct", "far_1pct"), core, attack, mcgill,
                outcomes_sink, source_sink, calibration_rows, eligibility_rows,
                None, args.repeats, True,
            )
            run_mcgill_conditions(
                mcgill_cache, ("far_5pct", "far_1pct"), core, attack, mcgill,
                outcomes_sink, calibration_rows, eligibility_rows, None, args.repeats,
            )
        outcomes_sink.close()
        source_sink.close()

        calibration = pd.DataFrame(calibration_rows)
        eligibility = pd.DataFrame(eligibility_rows)
        assert_partition_invariance(eligibility)
        calibration_export = calibration.copy()
        calibration_export["achieved_calibration_far_pct"] = 100 * calibration_export.pop("achieved_calibration_far")
        calibration_export["calibration_frr_pct"] = 100 * calibration_export.pop("calibration_frr")
        calibration_export.to_csv(output_dir / "calibration_by_claimant.csv", index=False)
        eligibility.to_csv(output_dir / "eligibility_by_path.csv", index=False)
        eligibility_summary = summarize_eligibility(eligibility)
        eligibility_summary.to_csv(output_dir / "eligibility_summary.csv", index=False)

        if args.mode == "full":
            selected_columns = [
                "dataset", "condition", "fold", "victim", "repeat", "strategy", "K", "method",
                *SUMMARY_METRICS, "initial_gate_width", "gate_state_count",
                "gate_stricter_state_count", "tau_auth_ge_mu_count",
                "accepted_blocked_by_gate_count",
            ]
            outcomes = pd.read_parquet(output_dir / "outcomes_by_path.parquet", columns=selected_columns)
            victims = victim_level(outcomes)
            operating, effects_subject, effects_bootstrap = make_summaries(
                victims, args.bootstrap_draws, 20261004,
            )
            operating, effects_bootstrap = complete_summary_grid(
                operating, effects_bootstrap, eligibility_summary,
            )
            gate = make_gate_diagnostics(outcomes, calibration)
            two_way = two_way_bootstrap(
                output_dir / "probe_outcomes_by_source.parquet", args.bootstrap_draws, 20261004,
            )
            operating.to_csv(output_dir / "operating_point_summary.csv", index=False)
            effects_subject.to_csv(output_dir / "effects_by_subject.csv", index=False)
            effects_bootstrap.to_csv(output_dir / "paired_effects_bootstrap.csv", index=False)
            gate.to_csv(output_dir / "gate_diagnostics.csv", index=False)
            two_way.to_csv(output_dir / "two_way_sensitivity.csv", index=False)
            figures = make_figures(output_dir, calibration, eligibility_summary, operating, effects_bootstrap, gate)
            make_report(
                output_dir, reference_frame, calibration, eligibility_summary,
                operating, effects_bootstrap, gate, two_way, args.mode,
            )
        else:
            make_report(
                output_dir, reference_frame, calibration, eligibility_summary,
                pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), args.mode,
            )
        status = "complete"
        return output_dir
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        (output_dir / "discrepancy_report.md").write_text(
            "# Stopped operating-point sensitivity run\n\n"
            f"The run stopped before completion: `{error}`\n\n"
            "```text\n" + traceback.format_exc() + "\n```\n",
            encoding="utf-8",
        )
        raise
    finally:
        outcomes_sink.close()
        source_sink.close()
        manifest = {
            "protocol_id": PROTOCOL_ID,
            "status": status,
            "mode": args.mode,
            "created_at": utc_now(),
            "command": shlex.join(sys.argv),
            "git_revision": git_revision(project_dir),
            "protocol_path": str(protocol_path.relative_to(project_dir)),
            "protocol_sha256": protocol_hash,
            "source_path": "src/paper3_operating_point_sensitivity.py",
            "source_sha256": sha256_file(Path(__file__).resolve()),
            "input_cache_sha256": cache_hashes,
            "seeds": {"attack": 4242, "bootstrap": 20261004},
            "repeats": args.repeats,
            "bootstrap_draws": args.bootstrap_draws,
            "conditions_evaluated": ["reference"] if args.mode == "reference" else list(CONDITIONS),
            "reference_reproduction_status": (
                "pass" if reference_rows and all(row["status"] == "pass" for row in reference_rows)
                else ("fail" if reference_rows else "not_completed")
            ),
            "cohort_definitions": {
                "random": "all structurally valid planned paths",
                "boundary_curves": "condition-specific common K8-feasible paths",
                "hmog_reference": "legacy common boundary-K8-feasible cohort for both strategies",
                "mcgill_reference": "all random paths and boundary-K8-feasible paths",
            },
            "output_units": {"granular_rates": "fractions", "summary_rates": "percent_or_percentage_points"},
            "output_schemas": {
                "outcomes_by_path.parquet": "one method outcome per dataset/condition/path/strategy/K",
                "probe_outcomes_by_source.parquet": "primary HMOG far_1pct boundary K8 source counts",
                "eligibility_by_path.csv": "one row per dataset/condition/planned path",
            },
            "row_counts": {
                "outcomes_by_path": outcomes_sink.rows,
                "probe_outcomes_by_source": source_sink.rows,
                "calibration": len(calibration_rows),
                "eligibility": len(eligibility_rows),
            },
            "figures": figures,
            "environment": {
                "python": sys.version, "platform": platform.platform(),
                "numpy": np.__version__, "pandas": pd.__version__, "pyarrow": pa.__version__,
            },
            "error": error,
        }
        # Hash the completed payload before writing the self-excluding manifest.
        manifest["generated_files"] = output_hashes(output_dir)
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", default=".")
    parser.add_argument(
        "--mcgill-cache",
        default="/Users/madigali/Downloads/McGillGait/paper3_external_cache_v1/scores_mcgill_day2.npz",
    )
    parser.add_argument("--mode", choices=("reference", "full"), default="full")
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument("--bootstrap-draws", type=int, default=10000)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    if args.repeats < 1 or args.repeats > 100:
        parser.error("--repeats must be in [1,100]")
    if args.mode == "full" and args.repeats != 100:
        parser.error("The locked full run requires exactly 100 repeats")
    if args.mode == "full" and args.bootstrap_draws != 10000:
        parser.error("The locked full run requires exactly 10000 bootstrap draws")
    return args


if __name__ == "__main__":
    destination = run(parse_args())
    print(f"Saved operating-point sensitivity package: {destination}")
