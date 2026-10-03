from __future__ import annotations

import copy
from pathlib import Path

import numpy as np

import paper3_external_mcgill as external


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "experiments" / "external_replication_mcgill.json"


def protocol() -> dict:
    return external.load_protocol(PROTOCOL_PATH)


def test_day1_split_is_chronological_and_complete():
    windows = np.arange(200 * 2, dtype=np.float32).reshape(200, 1, 2)
    train, validation, enrollment = external.chronological_day1_split(windows)
    assert (len(train), len(validation), len(enrollment)) == (120, 40, 40)
    np.testing.assert_array_equal(train[-1], windows[119])
    np.testing.assert_array_equal(validation[0], windows[120])
    np.testing.assert_array_equal(enrollment[0], windows[160])


def test_temporal_selection_is_unique_ordered_and_spans_day():
    indices = external.temporal_selection_indices(179, 160)
    assert len(indices) == len(np.unique(indices)) == 160
    assert indices[0] == 0
    assert indices[-1] == 178
    assert np.all(np.diff(indices) > 0)


def test_source_identity_split_is_disjoint_and_deterministic():
    sources = list(range(2, 21))
    first = external.split_source_identities(sources, np.random.default_rng(42), 0.5)
    second = external.split_source_identities(sources, np.random.default_rng(42), 0.5)
    poison, probe = first
    assert set(poison).isdisjoint(set(probe))
    assert set(poison) | set(probe) == set(sources)
    np.testing.assert_array_equal(first[0], second[0])
    np.testing.assert_array_equal(first[1], second[1])


def test_source_temporal_pool_uses_requested_half_only():
    subjects = np.repeat([1, 2], 6)
    within = np.tile(np.arange(6), 2)
    first = external.source_temporal_pool(subjects, within, [1, 2], half="first")
    second = external.source_temporal_pool(subjects, within, [1, 2], half="second")
    assert set(first).isdisjoint(set(second))
    assert set(first) | set(second) == set(range(12))
    assert np.all(within[first] < 3)
    assert np.all(within[second] >= 3)


def test_nested_poison_budgets_are_prefixes():
    pool = np.arange(100)
    scores = np.linspace(0.0, 1.0, 100)
    sequence = external.choose_poison_sequence(
        "random", pool, scores, 0.5, 8, np.random.default_rng(4242)
    )
    for budget in (0, 1, 2, 4, 8):
        np.testing.assert_array_equal(sequence[:budget], sequence[:8][:budget])


def test_boundary_attack_selects_smallest_positive_margins():
    pool = np.arange(8)
    scores = np.asarray([0.9, 0.51, 0.8, 0.49, 0.52, 0.7, 0.53, 0.6])
    sequence = external.choose_poison_sequence(
        "boundary", pool, scores, 0.5, 4, np.random.default_rng(0)
    )
    np.testing.assert_array_equal(sequence, np.asarray([1, 4, 6, 7]))


def test_frozen_never_updates_and_blind_updates_accepted_scores():
    cfg = protocol()
    enrollment = np.asarray([0.8, 0.82, 0.84, 0.86])
    frozen = external.evaluate_attack_method(
        "Frozen", enrollment, 0.7, np.asarray([0.71, 0.72]),
        np.asarray([0.7]), np.asarray([0.8]), cfg,
    )
    blind = external.evaluate_attack_method(
        "Blind EMA", enrollment, 0.7, np.asarray([0.71, 0.72]),
        np.asarray([0.7]), np.asarray([0.8]), cfg,
    )
    assert frozen["malicious_updates"] == 0
    assert frozen["mean_delta"] == 0
    assert blind["malicious_updates"] == 2
    assert blind["mean_delta"] != 0


def test_guarded_lambda_zero_reproduces_blind():
    cfg = copy.deepcopy(protocol())
    cfg["profile"]["guarded_lambda"] = 0.0
    enrollment = np.asarray([0.8, 0.82, 0.84, 0.86])
    poison = np.asarray([0.71, 0.72, 0.9, 0.1])
    probe = np.asarray([0.6, 0.7, 0.8])
    genuine = np.asarray([0.75, 0.85])
    blind = external.evaluate_attack_method(
        "Blind EMA", enrollment, 0.7, poison, probe, genuine, cfg
    )
    guarded = external.evaluate_attack_method(
        "Guarded EMA", enrollment, 0.7, poison, probe, genuine, cfg
    )
    for field in (
        "post_ASR", "post_FRR", "HTER", "malicious_updates", "MUR",
        "mean_after", "sigma_after", "threshold_after",
    ):
        assert np.isclose(float(blind[field]), float(guarded[field]), atol=1e-12)


def test_oracle_all_updates_rejected_genuine_without_granting_access():
    profile = external.EMAProfile.from_enrollment(
        [0.8, 0.82, 0.84], 0.7, alpha=0.05, min_sigma=1e-4
    )
    before = profile.mu
    accepted, updates = external.apply_stream(
        profile, [0.1], "Oracle-all-genuine", 0.82, 0.25, genuine=True
    )
    assert accepted == 0
    assert updates == 1
    assert profile.mu < before


def test_threshold_calibration_uses_higher_threshold_on_tie():
    genuine = np.asarray([0.8, 0.9])
    impostor = np.asarray([0.1, 0.2])
    threshold = external.calibrate_threshold(genuine, impostor)
    assert 0.2 < threshold < 0.8


def test_subject_bootstrap_is_deterministic():
    values = np.asarray([1.0, 2.0, 3.0, 4.0])
    first = external.bootstrap_mean(values, 1000, np.random.default_rng(9))
    second = external.bootstrap_mean(values, 1000, np.random.default_rng(9))
    assert first == second


def test_synthetic_smoke_passes():
    result = external.run_synthetic_smoke(PROTOCOL_PATH)
    assert result["status"] == "passed"
    assert result["guarded_updates"] < result["blind_updates"]
