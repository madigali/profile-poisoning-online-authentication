import math

import numpy as np

import paper3_guarded_adaptation as guarded


class DummyEMA:
    def __init__(self, mean=0.8, threshold=0.5, alpha=0.1):
        self.mean = mean
        self.second_moment = mean * mean + 0.01
        self._threshold = threshold
        self.alpha = alpha

    @property
    def threshold(self):
        return self._threshold

    def decide(self, score):
        accepted = score >= self.threshold
        if accepted:
            self.mean = (1 - self.alpha) * self.mean + self.alpha * score
            self.second_moment = (
                (1 - self.alpha) * self.second_moment + self.alpha * score * score
            )
        return accepted


def test_gate_endpoints():
    agent = DummyEMA()
    assert guarded.update_threshold(agent, 0.8, 0.0) == 0.5
    assert guarded.update_threshold(agent, 0.8, 1.0) == 0.8


def test_guarded_zero_matches_blind_stream():
    scores = [0.51, 0.7, 0.49, 0.9]
    blind = DummyEMA()
    zero = DummyEMA()
    blind_policy = guarded.Policy("blind", "Blind EMA", -1.0)
    zero_policy = guarded.Policy("guarded_0.00", "Guarded EMA", 0.0)
    assert guarded.process_stream(blind_policy, blind, scores, 0.8, genuine=False) == \
        guarded.process_stream(zero_policy, zero, scores, 0.8, genuine=False)
    assert blind.mean == zero.mean
    assert blind.second_moment == zero.second_moment


def test_guard_blocks_boundary_but_allows_high_confidence():
    policy = guarded.Policy("guarded_0.50", "Guarded EMA", 0.5)
    agent = DummyEMA()
    accepted, updates = guarded.process_stream(
        policy, agent, [0.51, 0.64, 0.65, 0.9], 0.8, genuine=False
    )
    assert accepted == 4
    assert updates == 2


def test_oracle_blocks_malicious_and_updates_genuine():
    policy = guarded.Policy("oracle", "Oracle EMA", -1.0)
    malicious = DummyEMA()
    assert guarded.process_stream(policy, malicious, [0.6, 0.9], 0.8, genuine=False) == (2, 0)
    assert math.isclose(malicious.mean, 0.8)
    genuine = DummyEMA()
    assert guarded.process_stream(policy, genuine, [0.6, 0.9], 0.8, genuine=True) == (2, 2)
    assert not math.isclose(genuine.mean, 0.8)


def test_frozen_never_updates():
    policy = guarded.Policy("frozen", "Frozen", -1.0)
    agent = DummyEMA()
    assert guarded.process_stream(policy, agent, [0.6, 0.9], 0.8, genuine=True) == (2, 0)
    assert np.isclose(agent.mean, 0.8)
