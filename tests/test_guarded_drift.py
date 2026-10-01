import numpy as np
import pandas as pd

import paper3_guarded_drift as drift


class DummyEMA:
    def __init__(self):
        self.mean = 0.8
        self.second_moment = 0.65
        self.alpha = 0.1


def test_session_pairs_are_disjoint_and_ordered():
    indices = np.arange(10)
    session = np.repeat([1, 2, 3, 4, 5], 2)
    within = np.tile([0, 10], 5)
    pairs = drift.session_pairs(indices, session, within)
    assert pairs == [(1, 0, 1), (2, 2, 3), (3, 4, 5), (4, 6, 7), (5, 8, 9)]


def test_early_late_partition_uses_endpoints_only():
    early, late = drift.split_early_late([False, True, False, True, True])
    assert early.tolist() == [False, True]
    assert late.tolist() == [True, True]


def test_force_ema_update_ignores_authentication_gate():
    agent = DummyEMA()
    drift.force_ema_update(agent, 0.2)
    assert np.isclose(agent.mean, 0.74)
    assert np.isclose(agent.second_moment, 0.589)


def test_frozen_gain_is_zero_and_pairing_is_subject_specific():
    frame = pd.DataFrame([
        {"fold": 1, "scenario": "global", "D": 1.0, "sid": 0,
         "policy_id": "frozen", "early_FRR": .7, "late_FRR": .6, "HTER": .5},
        {"fold": 1, "scenario": "global", "D": 1.0, "sid": 0,
         "policy_id": "guarded_0.25", "early_FRR": .6, "late_FRR": .4, "HTER": .35},
        {"fold": 1, "scenario": "global", "D": 1.0, "sid": 1,
         "policy_id": "frozen", "early_FRR": .3, "late_FRR": .2, "HTER": .3},
        {"fold": 1, "scenario": "global", "D": 1.0, "sid": 1,
         "policy_id": "guarded_0.25", "early_FRR": .4, "late_FRR": .3, "HTER": .4},
    ])
    out = drift.add_frozen_gains(frame)
    frozen = out[out.policy_id == "frozen"]
    assert np.allclose(frozen.adaptation_gain, 0)
    guarded = out[out.policy_id == "guarded_0.25"].sort_values("sid")
    assert np.allclose(guarded.adaptation_gain, [.2, -.1])
    assert np.allclose(guarded.hter_gain, [.15, -.1])


def test_subject_bootstrap_is_deterministic_and_paired():
    rows = []
    for sid in range(8):
        for policy, offset in [("frozen", 0.0), ("guarded_0.25", -0.1)]:
            rows.append({
                "scenario": "claimant_only", "D": 2.0, "sid": sid,
                "policy_id": policy, "method": "Frozen" if policy == "frozen" else "Guarded EMA",
                "lambda": "" if policy == "frozen" else "0.25",
                "lambda_value": -1.0 if policy == "frozen" else .25,
                "late_FRR": .5 + offset, "HTER": .4 + offset,
                "late_FAR": .2, "GUR": 0 if policy == "frozen" else .6,
            })
    frame = pd.DataFrame(rows)
    one = drift.paired_subject_bootstrap(frame, 200, 9)
    two = drift.paired_subject_bootstrap(frame, 200, 9)
    pd.testing.assert_frame_equal(one, two)
    gain = one[(one.policy_id == "guarded_0.25") & (one.effect == "late_FRR_gain")]
    assert np.isclose(gain.iloc[0].estimate, .1)
