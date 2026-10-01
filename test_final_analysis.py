import json
from pathlib import Path

import numpy as np
import pandas as pd

import paper3_final_analysis as final


def test_poisoning_data_selects_frozen_blind_and_guarded_and_checks_attack_v2():
    attack_rows = []
    guarded_rows = []
    for strategy in ["random", "boundary"]:
        for budget in [0, 1]:
            frozen = 20.0
            blind = 20.0 + 5.0 * budget
            for metric, value in [
                ("frozen_post_ASR", frozen),
                ("ema_blind_post_ASR", blind),
            ]:
                attack_rows.append({
                    "strategy": strategy, "K": budget, "metric": metric,
                    "mean": value, "ci95_low": value - 1, "ci95_high": value + 1,
                })
            for policy_id, method, value in [
                ("frozen", "Frozen", frozen),
                ("blind", "Blind EMA", blind),
                ("guarded_0.25", "Guarded EMA", 20.0),
            ]:
                guarded_rows.append({
                    "strategy": strategy, "K": budget, "policy_id": policy_id,
                    "method": method, "metric": "post_ASR", "mean": value,
                    "ci95_low": value - 1, "ci95_high": value + 1,
                })
    output = final.build_poisoning_plot_data(
        pd.DataFrame(attack_rows), pd.DataFrame(guarded_rows)
    )
    assert set(output["policy_id"]) == {"frozen", "blind", "guarded_0.25"}
    assert len(output) == 12
    assert output.query("strategy == 'boundary' and K == 1 and policy_id == 'blind'")[
        "mean"
    ].item() == 25.0


def test_poisoning_data_rejects_baseline_mismatch():
    attack = pd.DataFrame([
        {"strategy": "boundary", "K": 8, "metric": "frozen_post_ASR",
         "mean": 20.0, "ci95_low": 19.0, "ci95_high": 21.0},
        {"strategy": "boundary", "K": 8, "metric": "ema_blind_post_ASR",
         "mean": 40.0, "ci95_low": 39.0, "ci95_high": 41.0},
    ])
    guarded = pd.DataFrame([
        {"strategy": "boundary", "K": 8, "policy_id": "frozen",
         "method": "Frozen", "metric": "post_ASR", "mean": 21.0,
         "ci95_low": 20.0, "ci95_high": 22.0},
        {"strategy": "boundary", "K": 8, "policy_id": "blind",
         "method": "Blind EMA", "metric": "post_ASR", "mean": 40.0,
         "ci95_low": 39.0, "ci95_high": 41.0},
        {"strategy": "boundary", "K": 8, "policy_id": "guarded_0.25",
         "method": "Guarded EMA", "metric": "post_ASR", "mean": 20.0,
         "ci95_low": 19.0, "ci95_high": 21.0},
    ])
    try:
        final.build_poisoning_plot_data(attack, guarded)
    except AssertionError as exc:
        assert "baseline" in str(exc).lower()
    else:
        raise AssertionError("mismatched attack baseline was accepted")


def test_subject_bootstrap_is_deterministic_and_keeps_percent_units():
    frame = pd.DataFrame([
        {"sid": sid, "policy_id": policy, "method": method,
         "late_FAR": far + sid, "late_FRR": frr + sid}
        for sid in range(4)
        for policy, method, far, frr in [
            ("frozen", "Frozen", 20.0, 30.0),
            ("blind", "Blind EMA", 21.0, 29.0),
        ]
    ])
    first = final.build_tradeoff_plot_data(frame, 500, 123)
    second = final.build_tradeoff_plot_data(frame, 500, 123)
    pd.testing.assert_frame_equal(first, second)
    assert first.set_index("policy_id").loc["frozen", "late_FAR"] == 21.5
    assert first.set_index("policy_id").loc["frozen", "late_FRR"] == 31.5


def test_selection_trajectory_uses_subject_level_fold_average():
    checkpoints = pd.DataFrame([
        {"fold": fold, "scenario": "claimant_only", "D": 2.0, "sid": sid,
         "policy_id": policy, "method": method, "checkpoint": checkpoint,
         "mean": base + 0.01 * checkpoint + 0.001 * fold,
         "threshold": base / 2 + 0.005 * checkpoint + 0.001 * fold,
         "updated": update}
        for fold in [1, 2]
        for sid in [0, 1]
        for policy, method, base, update in [
            ("guarded_0.25", "Guarded EMA", 0.10, 0.5),
            ("oracle_all", "Oracle-all-genuine", 0.08, 1.0),
        ]
        for checkpoint in [0, 1]
    ])
    subject_fold = checkpoints[["fold", "scenario", "D", "sid", "policy_id"]].drop_duplicates()
    subject_fold["mean_before"] = 0.09
    subject_fold["threshold_before"] = 0.04
    output = final.build_selection_trajectory_data(
        checkpoints, subject_fold, n_bootstrap=200, seed=99
    )
    guarded_first = output.query(
        "policy_id == 'guarded_0.25' and checkpoint == 0 and metric == 'mean_delta'"
    ).iloc[0]
    assert np.isclose(guarded_first["estimate"], 0.0115)
    update = output.query(
        "policy_id == 'oracle_all' and checkpoint == 1 and metric == 'update_rate'"
    ).iloc[0]
    assert update["estimate"] == 100.0
    assert update["n_subjects"] == 2


def test_stopped_outer_statuses_must_be_false(tmp_path: Path):
    tq = tmp_path / "tq.json"
    quantile = tmp_path / "quantile.json"
    tq.write_text(json.dumps({"status": "validation_failed", "outer_test_loaded": False}))
    quantile.write_text(json.dumps({"status": "validation_failed", "outer_test_loaded": False}))
    final.validate_stopped_run(tq, "TQ-EMA v2")
    quantile.write_text(json.dumps({"status": "validation_failed", "outer_test_loaded": True}))
    try:
        final.validate_stopped_run(quantile, "Quantile")
    except AssertionError as exc:
        assert "outer" in str(exc).lower()
    else:
        raise AssertionError("loaded outer test was not rejected")


def test_final_summary_has_frozen_decision_rows():
    table = final.build_summary_table()
    assert list(table.columns) == [
        "Experiment", "Security result", "Drift utility", "Decision"
    ]
    assert list(table["Experiment"]) == [
        "Blind EMA", "Guarded EMA", "Oracle-all EMA", "TQ-EMA v1",
        "TQ-EMA v2", "Adaptive Quantile",
    ]
    assert table["Decision"].str.len().gt(0).all()
