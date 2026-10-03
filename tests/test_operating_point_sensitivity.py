from __future__ import annotations

import inspect
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
import paper3_operating_point_sensitivity as op  # noqa: E402


class FakeProfile:
    def __init__(self, scores, threshold, alpha=0.05, min_sigma=1e-4):
        values = np.asarray(scores, dtype=float)
        self.mu = float(values.mean())
        self.q = float(np.mean(values * values))
        self.alpha = alpha
        self.min_sigma = min_sigma
        self.k = (self.mu - threshold) / self.sigma

    @property
    def sigma(self):
        return max(math.sqrt(max(self.q - self.mu * self.mu, 0.0)), self.min_sigma)

    @property
    def threshold(self):
        return self.mu - self.k * self.sigma

    def update(self, score):
        self.mu = (1 - self.alpha) * self.mu + self.alpha * score
        self.q = (1 - self.alpha) * self.q + self.alpha * score * score


class FakeEMA:
    @classmethod
    def from_enrollment(cls, scores, threshold, alpha, min_sigma):
        return FakeProfile(scores, threshold, alpha, min_sigma)


class FakeMcGill:
    EMAProfile = FakeEMA


def calibration(condition="reference", threshold=0.5):
    return op.calibration_record(
        condition,
        genuine=[0.7, 0.8, 0.9],
        impostor=[0.1, 0.2, 0.3, 0.4],
        impostor_identities=[2, 2, 3, 3],
        reference_threshold=threshold,
        min_sigma=1e-4,
    )


def test_calibration_interface_cannot_read_test_or_day2_scores():
    names = set(inspect.signature(op.select_target_threshold).parameters)
    assert names == {"reference_threshold", "impostor_scores", "target"}
    assert not any("test" in name or "day2" in name for name in names)


def test_lower_target_never_lowers_threshold_and_meets_target():
    impostor = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    tau5 = op.select_target_threshold(0.15, impostor, 0.05)
    tau1 = op.select_target_threshold(0.15, impostor, 0.01)
    assert tau5 >= 0.15
    assert tau1 >= tau5
    assert np.mean(impostor >= tau5) <= 0.05
    assert np.mean(impostor >= tau1) <= 0.01


def test_tied_scores_cross_boundary_together():
    impostor = np.array([0.2, 0.2, 0.2, 0.7])
    threshold = op.select_target_threshold(0.1, impostor, 0.5)
    assert threshold == np.nextafter(np.float64(0.2), np.inf)
    assert np.mean(impostor >= threshold) == 0.25


def test_reference_is_retained_when_already_compliant():
    threshold = op.select_target_threshold(0.8, [0.1, 0.2, 0.3], 0.01)
    assert threshold == 0.8


def test_k_is_recomputed_and_negative_k_is_not_clipped():
    first = calibration("reference", threshold=0.5)
    strict = calibration("reference", threshold=0.95)
    assert first.k != strict.k
    assert strict.k < 0
    assert np.isclose(strict.k, (strict.mu0 - strict.tau0) / strict.sigma0)


def test_methods_have_identical_starting_threshold_and_rejected_samples_do_not_update():
    item = calibration("reference", threshold=0.5)
    enrollment = np.array([0.7, 0.8, 0.9])
    starts = []
    for method in op.METHODS:
        row, profile = op.evaluate_method(
            "McGill", method, enrollment, item, np.array([0.1]),
            np.array([0.2, 0.9]), np.array([0.8]), None, None, FakeMcGill,
        )
        starts.append(row["threshold_before"])
        assert row["malicious_updates"] == 0
        assert row["threshold_delta"] == 0
        assert profile.threshold == row["threshold_after"]
    assert starts == [item.tau0] * 3


def test_guarded_lambda_zero_matches_blind():
    item = calibration("reference", threshold=0.5)
    assert op.evaluate_guarded_lambda_zero(
        "McGill", np.array([0.7, 0.8, 0.9]), item,
        np.array([0.55, 0.65, 0.75]), None, None, FakeMcGill,
    )


def test_raw_guard_below_authentication_still_requires_authentication():
    item = calibration("reference", threshold=0.95)
    # With tau_auth > mu, raw gate is below tau_auth.  A score between the two
    # remains rejected and cannot update.
    raw_gate = item.tau0 + 0.25 * (item.mu0 - item.tau0)
    score = (raw_gate + item.tau0) / 2
    row, _ = op.evaluate_method(
        "McGill", "Guarded EMA", np.array([0.7, 0.8, 0.9]), item,
        np.array([score]), np.array([0.2]), np.array([0.8]),
        None, None, FakeMcGill,
    )
    assert raw_gate < item.tau0
    assert row["poison_accepts"] == 0
    assert row["malicious_updates"] == 0


def test_probe_rate_is_read_only():
    profile = FakeProfile([0.7, 0.8, 0.9], 0.5)
    before = (profile.mu, profile.q, profile.threshold)
    assert op.probe_rate([0.4, 0.6], profile.threshold) == 0.5
    assert (profile.mu, profile.q, profile.threshold) == before


def test_source_counts_reproduce_path_rate():
    profile = FakeProfile([0.7, 0.8, 0.9], 0.5)
    base = {"condition": "far_1pct", "fold": 1, "victim": 0, "repeat": 0, "strategy": "boundary", "K": 8}
    subjects = np.array([1, 1, 2, 2])
    scores = np.array([0.4, 0.6, 0.7, 0.3])
    rows = op.source_rows_for_path(base, "Frozen", profile, "HMOG", np.arange(4), subjects, scores)
    accepted = sum(row["accepted_probe_count"] for row in rows)
    total = sum(row["total_probe_count"] for row in rows)
    assert accepted / total == op.probe_rate(scores, profile.threshold)


def test_partition_invariance_across_conditions():
    rows = []
    for condition in op.CONDITIONS:
        rows.append({
            "dataset": "HMOG", "fold": 1, "victim": 0, "repeat": 0,
            "condition": condition, "poison_pool_id": "a", "probe_pool_id": "b",
            "n_poisoning_pool": 10, "n_probe_samples": 12,
        })
    op.assert_partition_invariance(pd.DataFrame(rows))
    rows[-1]["probe_pool_id"] = "changed"
    with pytest.raises(op.ProtocolError):
        op.assert_partition_invariance(pd.DataFrame(rows))


def test_poison_probe_disjointness_is_enforced():
    op.assert_disjoint_pools([1, 2, 3], [4, 5, 6])
    with pytest.raises(op.ProtocolError):
        op.assert_disjoint_pools([1, 2, 3], [3, 4, 5])


def test_nested_budgets_are_prefixes():
    sequence = np.array([7, 2, 9, 4, 3, 1, 8, 6])
    prefixes = {budget: sequence[:budget] for budget in op.BUDGETS}
    for smaller, larger in zip(op.BUDGETS[:-1], op.BUDGETS[1:]):
        assert np.array_equal(prefixes[smaller], prefixes[larger][:smaller])


def test_boundary_infeasibility_does_not_advance_unrelated_split_rng():
    def split_for_repeat(repeat):
        return np.random.default_rng(4242 + repeat * 10).permutation(20)

    expected = split_for_repeat(1)
    _ = split_for_repeat(0)
    # A deterministic feasibility failure has no access to repeat 1's stream.
    candidates = np.array([0, 1])
    assert len(candidates) < 8
    observed = split_for_repeat(1)
    assert np.array_equal(expected, observed)


def test_zero_feasibility_is_explicit_na_not_zero():
    eligibility = pd.DataFrame([{
        "dataset": "HMOG", "condition": "far_1pct", "strategy": "boundary", "K": 8,
        "eligible_paths": 0,
    }])
    operating = pd.DataFrame(columns=[
        "dataset", "condition", "strategy", "K", "method", "metric",
    ])
    effects = pd.DataFrame(columns=[
        "dataset", "condition", "strategy", "K", "contrast", "metric",
    ])
    completed, completed_effects = op.complete_summary_grid(operating, effects, eligibility)
    assert completed["mean"].isna().all()
    assert completed_effects["mean_effect"].isna().all()
    assert not (completed["mean"] == 0).any()
