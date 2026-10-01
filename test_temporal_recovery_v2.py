import numpy as np
import pandas as pd

import paper3_temporal_recovery as v1
import paper3_temporal_recovery_v2 as v2


class DummyEMA:
    def __init__(self):
        self.mean = 0.8
        self.second_moment = 0.65
        self.k = 1.0
        self.alpha = 0.05

    @property
    def threshold(self):
        return v1.derived_threshold(self.mean, self.second_moment, self.k)


def config(**overrides):
    values = dict(
        band_sigma=0.75,
        confirmation_sessions=2,
        recovery_alpha=0.05,
        anchor_sigma=0.25,
    )
    values.update(overrides)
    return v1.TQConfig(**values)


def state(**overrides):
    return v2.RecoveryEpisodeEMA(
        DummyEMA(), np.asarray([0.7, 0.9]), 0.7, config(**overrides),
        episode_horizon=3,
    )


def snapshot(controller):
    agent = controller.agent
    return (agent.mean, agent.second_moment, agent.threshold)


def enter_episode(controller):
    first = controller.process(0.68, session_id=1)
    second = controller.process(0.67, session_id=2)
    assert first["authenticated"] == 0
    assert second["event"] == "recovery_update_episode_enter"
    assert controller.in_recovery_episode


def test_normal_state_matches_v1_trusted_behavior():
    controller = state()
    before = snapshot(controller)
    event = controller.process(0.95, session_id=1)
    assert event["event"] == "trusted_update"
    assert event["authenticated"] == 1
    assert event["updated"] == 1
    assert snapshot(controller) != before


def test_confirmed_downward_batch_enters_episode_without_granting_access():
    controller = state()
    enter_episode(controller)
    assert controller.episode_entries == 1
    assert controller.episode_remaining == 3
    assert controller.recovery_updates == 1


def test_upward_trusted_update_is_suppressed_during_episode():
    controller = state()
    enter_episode(controller)
    before = snapshot(controller)
    event = controller.process(0.95, session_id=3)
    assert event["event"] == "trusted_upward_suppressed"
    assert event["authenticated"] == 1
    assert event["updated"] == 0
    assert event["suppressed"] == 1
    assert snapshot(controller) == before
    assert controller.suppressed_conflicting_trusted_updates == 1
    assert controller.episode_remaining == 2


def test_authentication_threshold_is_not_changed_by_suppression():
    controller = state()
    enter_episode(controller)
    threshold = controller.threshold
    event = controller.process(0.95, session_id=3)
    assert event["threshold_before"] == threshold
    assert event["threshold_after"] == threshold


def test_episode_expires_after_three_following_session_observations():
    controller = state()
    enter_episode(controller)
    for session_id in [3, 4, 5]:
        controller.process(0.95, session_id=session_id)
    assert not controller.in_recovery_episode
    assert controller.episode_exits == 1
    event = controller.process(0.95, session_id=6)
    assert event["event"] == "trusted_update"
    assert event["updated"] == 1


def test_new_confirmation_refreshes_episode_horizon():
    controller = state()
    enter_episode(controller)
    controller.process(0.68, session_id=3)
    assert controller.episode_remaining == 2
    event = controller.process(0.67, session_id=4)
    assert event["event"] == "recovery_update_episode_enter"
    assert controller.episode_remaining == 3
    assert controller.episode_refreshes == 1


def test_clear_reject_resets_quarantine_but_not_episode_immediately():
    controller = state()
    enter_episode(controller)
    event = controller.process(0.10, session_id=3)
    assert event["event"] == "clear_reject"
    assert event["episode_after"] == 1
    assert controller.episode_remaining == 2


def test_preview_reports_upward_conflict_for_high_score():
    agent = DummyEMA()
    mean, threshold = v2.preview_moment_update(agent, 0.95, agent.alpha)
    assert mean > agent.mean
    assert threshold > agent.threshold or mean > agent.mean


def test_v2_selection_enforces_both_constraints_and_mechanism_tie_break():
    rows = [
        {
            "config_id": "far_unsafe", "late_FRR_gain": 0.2,
            "late_FAR_change": 0.02, "HTER_change": 0.0,
            "conflicting_trusted_suppression_rate": 0.2,
            "recovery_update_rate": 0.1, "confirmation_sessions": 2,
            "band_sigma": 0.75, "recovery_alpha": 0.05, "anchor_sigma": 0.25,
        },
        {
            "config_id": "hter_unsafe", "late_FRR_gain": 0.2,
            "late_FAR_change": 0.0, "HTER_change": 0.01,
            "conflicting_trusted_suppression_rate": 0.2,
            "recovery_update_rate": 0.1, "confirmation_sessions": 2,
            "band_sigma": 0.75, "recovery_alpha": 0.05, "anchor_sigma": 0.25,
        },
        {
            "config_id": "feasible_low_activation", "late_FRR_gain": 0.1,
            "late_FAR_change": 0.0, "HTER_change": 0.0,
            "conflicting_trusted_suppression_rate": 0.01,
            "recovery_update_rate": 0.01, "confirmation_sessions": 3,
            "band_sigma": 0.25, "recovery_alpha": 0.025, "anchor_sigma": 0.10,
        },
        {
            "config_id": "feasible_active", "late_FRR_gain": 0.1,
            "late_FAR_change": 0.005, "HTER_change": 0.002,
            "conflicting_trusted_suppression_rate": 0.05,
            "recovery_update_rate": 0.02, "confirmation_sessions": 2,
            "band_sigma": 0.50, "recovery_alpha": 0.05, "anchor_sigma": 0.25,
        },
    ]
    selected = v2.select_validation_config(pd.DataFrame(rows))
    assert selected["config_id"] == "feasible_active"


def test_v2_selection_fails_closed_without_feasible_configuration():
    frame = pd.DataFrame([{
        "config_id": "unsafe", "late_FRR_gain": 0.2,
        "late_FAR_change": 0.02, "HTER_change": 0.01,
        "conflicting_trusted_suppression_rate": 0.2,
        "recovery_update_rate": 0.1, "confirmation_sessions": 2,
        "band_sigma": 0.75, "recovery_alpha": 0.05, "anchor_sigma": 0.25,
    }])
    try:
        v2.select_validation_config(frame)
    except RuntimeError as exc:
        assert "No v2 configuration" in str(exc)
    else:
        raise AssertionError("v2 selection did not fail closed")
