import numpy as np
import pandas as pd

import paper3_temporal_recovery as tq


class DummyEMA:
    def __init__(self):
        self.mean = 0.8
        self.second_moment = 0.65
        self.k = 1.0
        self.alpha = 0.05

    @property
    def threshold(self):
        return tq.derived_threshold(self.mean, self.second_moment, self.k)


def config(**overrides):
    values = dict(
        band_sigma=0.75,
        confirmation_sessions=2,
        recovery_alpha=0.05,
        anchor_sigma=0.25,
    )
    values.update(overrides)
    return tq.TQConfig(**values)


def state(**overrides):
    return tq.TemporalQuarantineEMA(
        DummyEMA(), np.asarray([0.7, 0.9]), 0.7, config(**overrides)
    )


def snapshot(agent):
    return (agent.mean, agent.second_moment, agent.threshold)


def test_ordinary_accept_grants_access_without_profile_update():
    recovery = state()
    before = snapshot(recovery.agent)
    event = recovery.process(0.71, session_id=1)
    assert event["event"] == "ordinary_accept"
    assert event["authenticated"] == 1
    assert event["updated"] == 0
    assert snapshot(recovery.agent) == before


def test_single_rejected_candidate_is_quarantine_only():
    recovery = state()
    before = snapshot(recovery.agent)
    event = recovery.process(0.68, session_id=1)
    assert event["event"] == "recovery_candidate"
    assert event["authenticated"] == 0
    assert event["updated"] == 0
    assert event["quarantine_size_after"] == 1
    assert snapshot(recovery.agent) == before


def test_two_distinct_rejected_sessions_can_confirm_bounded_recovery():
    recovery = state()
    before = snapshot(recovery.agent)
    recovery.process(0.68, session_id=1)
    event = recovery.process(0.67, session_id=2)
    after = snapshot(recovery.agent)
    assert event["event"] == "recovery_update"
    assert event["authenticated"] == 0
    assert event["updated"] == 1
    assert after[0] < before[0]
    assert after[2] < before[2]
    assert abs(after[0] - before[0]) <= 0.10 * recovery.sigma_enroll + 1e-12
    assert abs(after[2] - before[2]) <= 0.05 * recovery.sigma_enroll + 1e-12
    assert after[2] >= recovery.tau_enroll - 0.25 * recovery.sigma_enroll - 1e-12
    assert np.isclose(
        after[2],
        tq.derived_threshold(recovery.agent.mean, recovery.agent.second_moment, recovery.agent.k),
    )


def test_clear_reject_resets_quarantine_without_touching_production():
    recovery = state()
    recovery.process(0.68, session_id=1)
    before = snapshot(recovery.agent)
    event = recovery.process(0.50, session_id=2)
    assert event["event"] == "clear_reject"
    assert event["quarantine_size_after"] == 0
    assert snapshot(recovery.agent) == before


def test_trusted_update_is_bounded_and_clears_quarantine():
    recovery = state()
    recovery.process(0.68, session_id=1)
    before = snapshot(recovery.agent)
    event = recovery.process(0.95, session_id=2)
    after = snapshot(recovery.agent)
    assert event["event"] == "trusted_update"
    assert event["authenticated"] == 1
    assert event["updated"] == 1
    assert event["quarantine_size_after"] == 0
    assert abs(after[0] - before[0]) <= 0.10 * recovery.sigma_enroll + 1e-12
    assert abs(after[2] - before[2]) <= 0.05 * recovery.sigma_enroll + 1e-12


def test_duplicate_session_evidence_is_rejected():
    recovery = state()
    recovery.process(0.68, session_id=1)
    try:
        recovery.process(0.67, session_id=1)
    except AssertionError as exc:
        assert "distinct sessions" in str(exc)
    else:
        raise AssertionError("duplicate recovery session was accepted")


def test_validation_selection_enforces_far_constraint_then_conservative_tie_rule():
    rows = [
        {
            "config_id": "unsafe", "late_FRR_gain": 0.30, "late_FAR_change": 0.02,
            "confirmation_sessions": 2, "band_sigma": 0.75,
            "recovery_alpha": 0.05, "anchor_sigma": 0.25,
        },
        {
            "config_id": "feasible_loose", "late_FRR_gain": 0.10,
            "late_FAR_change": 0.01, "confirmation_sessions": 2,
            "band_sigma": 0.50, "recovery_alpha": 0.05, "anchor_sigma": 0.25,
        },
        {
            "config_id": "feasible_conservative", "late_FRR_gain": 0.10,
            "late_FAR_change": 0.005, "confirmation_sessions": 3,
            "band_sigma": 0.25, "recovery_alpha": 0.025, "anchor_sigma": 0.10,
        },
    ]
    selected = tq.select_validation_config(pd.DataFrame(rows))
    assert selected["config_id"] == "feasible_conservative"
    assert selected["selection_status"] == "feasible"


def test_validation_selection_fails_closed_when_no_config_meets_far_constraint():
    frame = pd.DataFrame([{
        "config_id": "unsafe", "late_FRR_gain": 0.30, "late_FAR_change": 0.02,
        "confirmation_sessions": 2, "band_sigma": 0.75,
        "recovery_alpha": 0.05, "anchor_sigma": 0.25,
    }])
    try:
        tq.select_validation_config(frame)
    except RuntimeError as exc:
        assert "Delta-FAR" in str(exc)
    else:
        raise AssertionError("validation selection did not fail closed")


def test_validation_split_keeps_first_two_sessions_for_enrollment():
    y = np.repeat([0, 1], 10)
    session = np.tile(np.repeat([2, 7, 12, 17, 22], 2), 2)
    within = np.tile([0, 10], 10)
    enrollment, tuning = tq.validation_split(0, y, session, within)
    assert [row[0] for row in enrollment] == [2, 7]
    assert [row[0] for row in tuning] == [12, 17, 22]
    assert not ({index for _, a, p in enrollment for index in (a, p)}
                & {index for _, a, p in tuning for index in (a, p)})


def test_two_way_far_bootstrap_is_deterministic():
    rows = []
    for fold in [1, 2]:
        for victim in range(3):
            for source in range(3):
                if victim == source:
                    continue
                for checkpoint in range(4):
                    for policy, offset in [("frozen", 0.0), ("tq_ema", 0.01)]:
                        rows.append({
                            "fold": fold, "D": 2.0, "sid": victim,
                            "source_id": source, "checkpoint": checkpoint,
                            "policy_id": policy, "source_FAR": 0.2 + offset,
                        })
    frame = pd.DataFrame(rows)
    one = tq.two_way_far_bootstrap(frame, 200, 17)
    two = tq.two_way_far_bootstrap(frame, 200, 17)
    pd.testing.assert_frame_equal(one, two)
    assert np.isclose(one.iloc[0]["estimate"], 0.01)
