import numpy as np
import pandas as pd

import paper3_robust_quantile as quantile


def test_weighted_quantile_is_discrete_inverse_cdf_without_interpolation():
    scores = np.asarray([1.0, 2.0, 3.0, 4.0])
    equal = np.full(4, 0.25)
    assert quantile.weighted_quantile(scores, equal, 0.20) == 1.0
    assert quantile.weighted_quantile(scores, equal, 0.50) == 2.0
    skewed = np.asarray([0.1, 0.1, 0.1, 0.7])
    assert quantile.weighted_quantile(scores, skewed, 0.50) == 4.0


def test_initial_quantile_threshold_exactly_matches_eer_threshold():
    enrollment = np.asarray([0.20, 0.30, 0.40, 0.50, 0.60])
    profile = quantile.AdaptiveQuantileProfile(enrollment, tau0=0.25, rho=0.9)
    assert np.isclose(profile.threshold, 0.25, atol=1e-15, rtol=0)
    assert profile.q20 == 0.20
    assert profile.q50 == 0.40


def test_update_applies_declared_exponential_weights_and_renormalizes():
    profile = quantile.AdaptiveQuantileProfile(
        np.asarray([0.20, 0.40, 0.60, 0.80]), tau0=0.25, rho=0.8
    )
    profile.update(0.10)
    assert np.isclose(profile.weights.sum(), 1.0)
    assert np.allclose(profile.weights[:-1], np.full(4, 0.20))
    assert np.isclose(profile.weights[-1], 0.20)
    assert profile.scores[-1] == 0.10


def test_rejected_score_does_not_update_accepted_only_profile():
    profile = quantile.AdaptiveQuantileProfile(
        np.asarray([0.20, 0.30, 0.40, 0.50, 0.60]), tau0=0.25, rho=0.9
    )
    before = profile.snapshot()
    event = quantile.process_quantile_score(profile, 0.10, oracle_all=False)
    assert event["authenticated"] == 0
    assert event["updated"] == 0
    assert profile.snapshot() == before


def test_accepted_score_updates_accepted_only_profile():
    profile = quantile.AdaptiveQuantileProfile(
        np.asarray([0.20, 0.30, 0.40, 0.50, 0.60]), tau0=0.25, rho=0.9
    )
    before_n = len(profile.scores)
    event = quantile.process_quantile_score(profile, 0.55, oracle_all=False)
    assert event["authenticated"] == 1
    assert event["updated"] == 1
    assert len(profile.scores) == before_n + 1


def test_oracle_all_updates_rejected_genuine_score_without_granting_access():
    profile = quantile.AdaptiveQuantileProfile(
        np.asarray([0.20, 0.30, 0.40, 0.50, 0.60]), tau0=0.25, rho=0.9
    )
    event = quantile.process_quantile_score(profile, 0.10, oracle_all=True)
    assert event["authenticated"] == 0
    assert event["updated"] == 1
    assert profile.scores[-1] == 0.10


def test_identical_feedback_makes_accepted_and_oracle_profiles_identical():
    enrollment = np.asarray([0.20, 0.30, 0.40, 0.50, 0.60])
    accepted = quantile.AdaptiveQuantileProfile(enrollment, tau0=0.25, rho=0.9)
    oracle = quantile.AdaptiveQuantileProfile(enrollment, tau0=0.25, rho=0.9)
    for score in [0.55, 0.58, 0.52]:
        quantile.process_quantile_score(accepted, score, oracle_all=False)
        quantile.process_quantile_score(oracle, score, oracle_all=True)
    assert accepted.snapshot() == oracle.snapshot()


def test_near_zero_initial_quantile_span_fails_without_fallback():
    enrollment = np.full(10, 0.4)
    try:
        quantile.AdaptiveQuantileProfile(enrollment, tau0=0.3, rho=0.9)
    except quantile.InvalidQuantilePath as exc:
        assert "q50_0 - q20_0" in str(exc)
    else:
        raise AssertionError("degenerate quantile path did not fail")


def test_rho_selection_enforces_constraints_and_prefers_larger_rho_on_tie():
    frame = pd.DataFrame([
        {"rho": 0.80, "late_FRR_gain": 0.10, "late_FAR_change": 0.02,
         "HTER_change": 0.0},
        {"rho": 0.90, "late_FRR_gain": 0.05, "late_FAR_change": 0.005,
         "HTER_change": 0.002},
        {"rho": 0.95, "late_FRR_gain": 0.05, "late_FAR_change": 0.004,
         "HTER_change": 0.002},
    ])
    selected = quantile.select_rho(frame)
    assert selected["rho"] == 0.95
    assert selected["selection_status"] == "feasible"


def test_rho_selection_fails_closed_without_feasible_value():
    frame = pd.DataFrame([
        {"rho": 0.80, "late_FRR_gain": 0.10, "late_FAR_change": 0.02,
         "HTER_change": 0.0},
        {"rho": 0.90, "late_FRR_gain": 0.10, "late_FAR_change": 0.0,
         "HTER_change": 0.01},
    ])
    try:
        quantile.select_rho(frame)
    except RuntimeError as exc:
        assert "No Accepted-only Quantile rho" in str(exc)
    else:
        raise AssertionError("rho selection did not fail closed")


def test_feedback_contrast_pairs_only_identical_fold_and_rho():
    common = {
        "fold": 1, "rho": 0.9, "late_FAR": 0.2, "GUR": 0.5,
        "adaptation_auth_rate": 0.5, "late_FRR_gain": -0.1,
        "late_FAR_change": -0.05, "HTER_change": 0.025,
        "q20_delta": 0.01, "q50_delta": 0.02, "threshold_delta": 0.015,
        "n_subjects": 100,
    }
    frame = pd.DataFrame([
        {**common, "policy_id": "quantile_accepted", "late_FRR": 0.5,
         "HTER": 0.35},
        {**common, "policy_id": "quantile_oracle", "late_FRR": 0.3,
         "HTER": 0.25, "GUR": 1.0, "late_FRR_gain": 0.1,
         "HTER_change": -0.075},
    ])
    paired = quantile.feedback_contrast_table(frame)
    assert len(paired) == 1
    assert np.isclose(paired.loc[0, "censoring_FRR_cost"], 0.2)
    assert np.isclose(paired.loc[0, "censoring_HTER_cost"], 0.1)
    assert not bool(paired.loc[0, "accepted_feasible"])
