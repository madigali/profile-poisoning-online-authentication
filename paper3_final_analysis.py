#!/usr/bin/env python3
"""Read-only final aggregation for the frozen Paper 3 HMOG experiments.

This script never trains, scores, adapts, or tunes a model.  It validates and
combines already completed authoritative result files, then writes publication
figures, compact plot-data tables, a decision table, and a provenance manifest
to a new output directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FREEZE_TAG = "paper3-method-freeze-2026-10-02"
EXPECTED_BUDGETS = (0, 1, 2, 4, 8)
EXPECTED_ATTACKS = ("random", "boundary")
POISON_POLICIES = ("frozen", "blind", "guarded_0.25")
DRIFT_POLICIES = ("frozen", "blind", "guarded_0.25", "oracle_all", "tq_ema")

COLORS = {
    "frozen": "#4D4D4D",
    "blind": "#D55E00",
    "guarded_0.25": "#0072B2",
    "oracle_all": "#009E73",
    "tq_ema": "#CC79A7",
}
MARKERS = {
    "frozen": "o", "blind": "s", "guarded_0.25": "^",
    "oracle_all": "D", "tq_ema": "P",
}
LABELS = {
    "frozen": "Frozen",
    "blind": "Blind EMA",
    "guarded_0.25": "Guarded EMA (λ=0.25)",
    "oracle_all": "Oracle-all EMA",
    "tq_ema": "TQ-EMA v1",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_columns(frame: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing = set(columns).difference(frame.columns)
    if missing:
        raise KeyError(f"{label} missing required columns: {sorted(missing)}")


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_manifest(path: Path, expected_status: str, label: str) -> dict:
    payload = read_json(path)
    if payload.get("status") != expected_status:
        raise AssertionError(
            f"{label} manifest status={payload.get('status')!r}, "
            f"expected {expected_status!r}"
        )
    return payload


def validate_stopped_run(path: Path, label: str) -> dict:
    payload = read_json(path)
    if payload.get("status") != "validation_failed":
        raise AssertionError(f"{label} did not stop with validation_failed")
    if payload.get("outer_test_loaded") is not False:
        raise AssertionError(f"{label} outer test was loaded or status is missing")
    return payload


def build_poisoning_plot_data(
    attack_summary: pd.DataFrame,
    guarded_summary: pd.DataFrame,
) -> pd.DataFrame:
    require_columns(
        attack_summary,
        ["strategy", "K", "metric", "mean", "ci95_low", "ci95_high"],
        "attack v2 summary",
    )
    require_columns(
        guarded_summary,
        [
            "strategy", "K", "policy_id", "method", "metric", "mean",
            "ci95_low", "ci95_high",
        ],
        "guarded summary",
    )
    plot = guarded_summary[
        (guarded_summary["metric"] == "post_ASR")
        & guarded_summary["policy_id"].isin(POISON_POLICIES)
    ][
        [
            "strategy", "K", "policy_id", "method", "mean", "ci95_low",
            "ci95_high",
        ]
    ].copy()
    plot["method"] = plot["policy_id"].map(LABELS)
    plot["policy_order"] = plot["policy_id"].map(
        {policy: index for index, policy in enumerate(POISON_POLICIES)}
    )
    expected = {
        (attack, budget, policy)
        for attack in EXPECTED_ATTACKS
        for budget in EXPECTED_BUDGETS
        for policy in POISON_POLICIES
    }
    observed = set(plot[["strategy", "K", "policy_id"]].itertuples(index=False, name=None))
    if set(attack_summary["strategy"]) == set(EXPECTED_ATTACKS) and set(
        attack_summary["K"]
    ) == set(EXPECTED_BUDGETS) and observed != expected:
        raise AssertionError("Final poisoning data do not contain the complete policy grid")

    for policy_id, metric in [
        ("frozen", "frozen_post_ASR"),
        ("blind", "ema_blind_post_ASR"),
    ]:
        reference = attack_summary[attack_summary["metric"] == metric][
            ["strategy", "K", "mean"]
        ].rename(columns={"mean": "attack_v2_mean"})
        observed_baseline = plot[plot["policy_id"] == policy_id][
            ["strategy", "K", "mean"]
        ].rename(columns={"mean": "guarded_run_mean"})
        paired = reference.merge(
            observed_baseline,
            on=["strategy", "K"],
            how="inner",
            validate="one_to_one",
        )
        if len(paired) != len(reference) or not np.allclose(
            paired["attack_v2_mean"], paired["guarded_run_mean"],
            atol=1e-9, rtol=0.0,
        ):
            raise AssertionError(f"{policy_id} baseline mismatch between attack v2 and guarded run")
    return plot.sort_values(["strategy", "K", "policy_order"]).reset_index(drop=True)


def check_lambda_zero_sanity(tradeoff: pd.DataFrame) -> None:
    require_columns(
        tradeoff,
        ["strategy", "K", "policy_id", "post_ASR", "post_FRR", "HTER", "MUR"],
        "guarded trade-off",
    )
    metrics = ["post_ASR", "post_FRR", "HTER", "MUR"]
    blind = tradeoff[tradeoff["policy_id"] == "blind"][["strategy", "K"] + metrics]
    gate0 = tradeoff[tradeoff["policy_id"] == "guarded_0.00"][
        ["strategy", "K"] + metrics
    ]
    paired = blind.merge(
        gate0, on=["strategy", "K"], suffixes=("_blind", "_gate0"),
        validate="one_to_one",
    )
    for metric in metrics:
        if not np.allclose(
            paired[f"{metric}_blind"], paired[f"{metric}_gate0"],
            atol=1e-9, rtol=0.0,
        ):
            raise AssertionError(f"Guarded lambda=0 failed Blind EMA sanity check for {metric}")


def bootstrap_mean(values: np.ndarray, n_bootstrap: int, seed: int) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    if not len(array):
        raise ValueError("Cannot bootstrap an empty finite array")
    rng = np.random.default_rng(seed)
    draws = rng.choice(array, size=(n_bootstrap, len(array)), replace=True).mean(axis=1)
    return (
        float(array.mean()),
        float(np.quantile(draws, 0.025)),
        float(np.quantile(draws, 0.975)),
    )


def build_tradeoff_plot_data(
    by_subject: pd.DataFrame,
    n_bootstrap: int,
    seed: int,
) -> pd.DataFrame:
    require_columns(
        by_subject,
        ["sid", "policy_id", "method", "late_FAR", "late_FRR"],
        "TQ by-subject table",
    )
    rows: list[dict] = []
    for order, (policy_id, group) in enumerate(by_subject.groupby("policy_id", sort=False)):
        method = str(group["method"].iloc[0])
        material = hashlib.sha256(f"{seed}|{policy_id}".encode()).digest()
        method_seed = int.from_bytes(material[:8], "little")
        far, far_low, far_high = bootstrap_mean(
            group["late_FAR"].to_numpy(), n_bootstrap, method_seed
        )
        frr, frr_low, frr_high = bootstrap_mean(
            group["late_FRR"].to_numpy(), n_bootstrap, method_seed + 1
        )
        rows.append({
            "policy_id": policy_id,
            "method": LABELS.get(policy_id, method),
            "policy_order": order,
            "n_subjects": int(group["sid"].nunique()),
            "late_FAR": far,
            "late_FAR_ci95_low": far_low,
            "late_FAR_ci95_high": far_high,
            "late_FRR": frr,
            "late_FRR_ci95_low": frr_low,
            "late_FRR_ci95_high": frr_high,
        })
    return pd.DataFrame(rows).sort_values("policy_order").reset_index(drop=True)


def build_selection_trajectory_data(
    checkpoints: pd.DataFrame,
    subject_fold: pd.DataFrame,
    n_bootstrap: int,
    seed: int,
) -> pd.DataFrame:
    identity = ["fold", "scenario", "D", "sid", "policy_id"]
    require_columns(
        checkpoints,
        identity + ["method", "checkpoint", "mean", "threshold", "updated"],
        "clean-drift checkpoints",
    )
    require_columns(
        subject_fold,
        identity + ["mean_before", "threshold_before"],
        "clean-drift subject-fold table",
    )
    policies = ["guarded_0.25", "oracle_all"]
    paths = checkpoints[
        (checkpoints["scenario"] == "claimant_only")
        & np.isclose(checkpoints["D"], 2.0)
        & checkpoints["policy_id"].isin(policies)
    ].copy()
    baselines = subject_fold[
        (subject_fold["scenario"] == "claimant_only")
        & np.isclose(subject_fold["D"], 2.0)
        & subject_fold["policy_id"].isin(policies)
    ][identity + ["mean_before", "threshold_before"]].drop_duplicates(identity)
    paths = paths.merge(baselines, on=identity, how="left", validate="many_to_one")
    if paths[["mean_before", "threshold_before"]].isna().any().any():
        raise AssertionError("Missing trajectory enrollment baseline")
    paths["mean_delta"] = paths["mean"] - paths["mean_before"]
    paths["threshold_delta"] = paths["threshold"] - paths["threshold_before"]
    paths["update_rate"] = 100.0 * paths["updated"]

    # Folds overlap.  Average each subject across available folds before
    # estimating the population mean and subject-bootstrap interval.
    subject = paths.groupby(
        ["sid", "policy_id", "method", "checkpoint"], as_index=False
    )[["mean_delta", "threshold_delta", "update_rate"]].mean()
    rows: list[dict] = []
    for (policy_id, method, checkpoint), group in subject.groupby(
        ["policy_id", "method", "checkpoint"], sort=True
    ):
        for metric in ["mean_delta", "threshold_delta", "update_rate"]:
            material = hashlib.sha256(
                f"{seed}|{policy_id}|{checkpoint}|{metric}".encode()
            ).digest()
            metric_seed = int.from_bytes(material[:8], "little")
            estimate, low, high = bootstrap_mean(
                group[metric].to_numpy(), n_bootstrap, metric_seed
            )
            rows.append({
                "policy_id": policy_id,
                "method": LABELS.get(policy_id, str(method)),
                "checkpoint": int(checkpoint),
                "session_checkpoint": int(checkpoint) + 1,
                "metric": metric,
                "estimate": estimate,
                "ci95_low": low,
                "ci95_high": high,
                "n_subjects": int(group["sid"].nunique()),
            })
    return pd.DataFrame(rows).sort_values(
        ["metric", "policy_id", "checkpoint"]
    ).reset_index(drop=True)


def build_summary_table() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Experiment": "Blind EMA",
            "Security result": "Vulnerable: boundary poisoning raised ASR with budget; MUR reached 100%.",
            "Drift utility": "Weak: claimant-only D=2 late-FRR gain was +0.33 pp with higher FAR.",
            "Decision": "Reject as a deployable adaptive policy.",
        },
        {
            "Experiment": "Guarded EMA",
            "Security result": "Strong gate effect: λ=0.25 kept boundary K=8 ASR near Frozen and MUR at 1.63%.",
            "Drift utility": "Negative: claimant-only D=2 late-FRR gain was -2.07 pp; GUR was 59.05%.",
            "Decision": "Retain as the security baseline, not as a drift-utility claim.",
        },
        {
            "Experiment": "Oracle-all EMA",
            "Security result": "Not deployable: requires genuine labels and increased late FAR under D=2.",
            "Drift utility": "Diagnostic positive: D=2 late-FRR gain was +6.60 pp.",
            "Decision": "Use only to demonstrate recoverability and selection bias.",
        },
        {
            "Experiment": "TQ-EMA v1",
            "Security result": "Uses the guarded trusted path; combined drift-plus-attack was not evaluated.",
            "Drift utility": "No FRR recovery: gain -0.90 pp, 95% CI [-1.80, 0.00].",
            "Decision": "Stop this branch.",
        },
        {
            "Experiment": "TQ-EMA v2",
            "Security result": "Outer security evaluation not run after the validation gate failed.",
            "Drift utility": "Validation failed in fold 4; outer test remained unloaded.",
            "Decision": "Stop under the prespecified rule.",
        },
        {
            "Experiment": "Adaptive Quantile",
            "Security result": "Outer security evaluation not run after validation failed in all folds.",
            "Drift utility": "Accepted-only and Oracle-all quantile variants both remained worse than Frozen.",
            "Decision": "Stop this frozen q20/q50 representation.",
        },
    ])


def save_table_markdown(table: pd.DataFrame, path: Path) -> None:
    widths = {
        column: max(len(column), *(len(str(value)) for value in table[column]))
        for column in table.columns
    }
    header = "| " + " | ".join(column.ljust(widths[column]) for column in table.columns) + " |"
    rule = "| " + " | ".join("-" * widths[column] for column in table.columns) + " |"
    rows = [
        "| " + " | ".join(str(row[column]).ljust(widths[column]) for column in table.columns) + " |"
        for _, row in table.iterrows()
    ]
    path.write_text("\n".join([header, rule] + rows) + "\n", encoding="utf-8")


def configure_matplotlib() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.22,
        "grid.linewidth": 0.65,
        "lines.linewidth": 2.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.bbox": "tight",
    })


def save_figure(fig: plt.Figure, figure_dir: Path, stem: str) -> None:
    fig.savefig(figure_dir / f"{stem}.png", dpi=300, facecolor="white")
    fig.savefig(figure_dir / f"{stem}.pdf", facecolor="white")
    plt.close(fig)


def plot_poisoning(data: pd.DataFrame, figure_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.15), sharex=True, sharey=True)
    for axis, strategy, panel in zip(axes, ["random", "boundary"], ["a", "b"]):
        group = data[data["strategy"] == strategy]
        for policy_id in POISON_POLICIES:
            line = group[group["policy_id"] == policy_id].sort_values("K")
            x = line["K"].to_numpy(dtype=float)
            mean = line["mean"].to_numpy(dtype=float)
            low = line["ci95_low"].to_numpy(dtype=float)
            high = line["ci95_high"].to_numpy(dtype=float)
            axis.plot(
                x, mean, color=COLORS[policy_id], marker=MARKERS[policy_id],
                markersize=5.5, label=LABELS[policy_id],
            )
            axis.fill_between(x, low, high, color=COLORS[policy_id], alpha=0.12)
        axis.set_title(f"({panel}) {strategy.capitalize()} attack")
        axis.set_xlabel("Poisoning-update budget K")
        axis.set_xticks(EXPECTED_BUDGETS)
    axes[0].set_ylabel("Post-poison attack success rate (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle("Profile poisoning under nested attack budgets", y=0.98, fontsize=12)
    fig.legend(
        handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.915),
        ncol=3, frameon=False,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.80))
    save_figure(fig, figure_dir, "figure1_poisoning_asr")


def plot_tradeoff(data: pd.DataFrame, figure_dir: Path) -> None:
    fig, axis = plt.subplots(figsize=(6.7, 5.4))
    frozen = data[data["policy_id"] == "frozen"].iloc[0]
    axis.axvline(frozen["late_FAR"], color=COLORS["frozen"], alpha=0.35, linewidth=1)
    axis.axhline(frozen["late_FRR"], color=COLORS["frozen"], alpha=0.35, linewidth=1)
    offsets = {
        "frozen": (7, 7), "blind": (7, -15), "guarded_0.25": (7, 7),
        "oracle_all": (7, 7), "tq_ema": (7, -16),
    }
    for _, row in data.iterrows():
        policy = row["policy_id"]
        axis.errorbar(
            row["late_FAR"], row["late_FRR"],
            xerr=[[row["late_FAR"] - row["late_FAR_ci95_low"]],
                  [row["late_FAR_ci95_high"] - row["late_FAR"]]],
            yerr=[[row["late_FRR"] - row["late_FRR_ci95_low"]],
                  [row["late_FRR_ci95_high"] - row["late_FRR"]]],
            fmt=MARKERS[policy], color=COLORS[policy], markersize=8,
            capsize=3, elinewidth=1.2,
        )
        axis.annotate(
            row["method"], (row["late_FAR"], row["late_FRR"]),
            xytext=offsets[policy], textcoords="offset points", color=COLORS[policy],
            fontsize=9,
        )
    axis.set_xlabel("Late false acceptance rate (%)")
    axis.set_ylabel("Late false rejection rate (%)")
    axis.set_title("Security–adaptation trade-off under claimant-only drift (D=2)")
    axis.annotate(
        "Lower is better", xy=(0.02, 0.03), xycoords="axes fraction",
        color="#555555", fontsize=8.5,
    )
    fig.tight_layout()
    save_figure(fig, figure_dir, "figure2_security_adaptation_tradeoff")


def plot_selection_bias(data: pd.DataFrame, figure_dir: Path) -> None:
    metrics = [
        ("mean_delta", "Change in profile mean", "Score change"),
        ("threshold_delta", "Change in authentication threshold", "Score change"),
        ("update_rate", "Genuine update rate", "Update rate (%)"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.05), sharex=True)
    for axis, (metric, title, ylabel), panel in zip(axes, metrics, ["a", "b", "c"]):
        group = data[data["metric"] == metric]
        for policy_id in ["guarded_0.25", "oracle_all"]:
            line = group[group["policy_id"] == policy_id].sort_values("checkpoint")
            x = line["session_checkpoint"].to_numpy(dtype=float)
            estimate = line["estimate"].to_numpy(dtype=float)
            low = line["ci95_low"].to_numpy(dtype=float)
            high = line["ci95_high"].to_numpy(dtype=float)
            axis.plot(
                x, estimate, color=COLORS[policy_id], marker=MARKERS[policy_id],
                markersize=5.5, label=LABELS[policy_id],
            )
            axis.fill_between(x, low, high, color=COLORS[policy_id], alpha=0.13)
        if metric != "update_rate":
            axis.axhline(0.0, color="#777777", linewidth=0.9, alpha=0.55)
        axis.set_title(f"({panel}) {title}")
        axis.set_xlabel("Session checkpoint")
        axis.set_ylabel(ylabel)
        axis.set_xticks([1, 2, 3, 4, 5])
    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle(
        "Accepted-only feedback reverses adaptation under downward drift",
        y=0.98, fontsize=12,
    )
    fig.legend(
        handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.90),
        ncol=2, frameon=False,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.78))
    save_figure(fig, figure_dir, "figure3_selection_bias_mechanism")


def git_revision(source_dir: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=source_dir,
        check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def resolve_output_dir(source_dir: Path, requested: str | None) -> Path:
    if requested:
        path = Path(requested)
        if not path.is_absolute():
            path = Path.cwd() / path
    else:
        path = source_dir / "results" / f"{datetime.now():%Y%m%d-%H%M%S}-final-analysis"
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty output directory: {path}")
    return path.resolve()


def run(args: argparse.Namespace) -> Path:
    source_dir = Path(args.source_dir).resolve()
    output_dir = resolve_output_dir(source_dir, args.output_dir)
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    guarded_dir = source_dir / "results" / "paper3_guarded_20260930"
    drift_dir = source_dir / "results" / "paper3_oracle_all_drift_20261001_v2"
    tq_dir = source_dir / "results" / "paper3_tq_clean_drift_20261001_v1"
    tq_v2_dir = source_dir / "results" / "paper3_tq_v2_validation_failed_20261001"
    quantile_dir = source_dir / "results" / "paper3_quantile_validation_failed_20261001_v1"

    inputs = {
        "attack_v2_summary": source_dir / "paper3_attack_v2_summary.csv",
        "attack_v2_by_fold": source_dir / "paper3_attack_v2_by_fold.csv",
        "guarded_summary": guarded_dir / "paper3_guarded_summary.csv",
        "guarded_tradeoff": guarded_dir / "paper3_guarded_tradeoff.csv",
        "guarded_manifest": guarded_dir / "manifest.json",
        "guarded_exclusions": guarded_dir / "exclusions.csv",
        "drift_summary": drift_dir / "paper3_guarded_drift_summary.csv",
        "drift_by_subject": drift_dir / "paper3_guarded_drift_by_subject.csv",
        "drift_subject_fold": drift_dir / "paper3_guarded_drift_subject_fold.csv",
        "drift_checkpoints": drift_dir / "paper3_guarded_drift_checkpoints.csv",
        "drift_manifest": drift_dir / "manifest.json",
        "drift_exclusions": drift_dir / "exclusions.csv",
        "tq_summary": tq_dir / "paper3_tq_summary.csv",
        "tq_by_subject": tq_dir / "paper3_tq_by_subject.csv",
        "tq_primary": tq_dir / "primary_assessment.json",
        "tq_manifest": tq_dir / "manifest.json",
        "tq_exclusions": tq_dir / "exclusions.csv",
        "tq_v2_manifest": tq_v2_dir / "manifest.json",
        "tq_v2_failure": tq_v2_dir / "validation_failure.json",
        "tq_v2_selection": tq_v2_dir / "paper3_tq_v2_selected_by_fold.csv",
        "tq_v2_exclusions": tq_v2_dir / "exclusions.csv",
        "quantile_manifest": quantile_dir / "manifest.json",
        "quantile_failure": quantile_dir / "validation_failure.json",
        "quantile_selection": quantile_dir / "paper3_quantile_selected_by_fold.csv",
        "quantile_contrast": quantile_dir / "paper3_quantile_feedback_contrast.csv",
        "quantile_exclusions": quantile_dir / "exclusions.csv",
    }
    missing = [str(path) for path in inputs.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing authoritative inputs:\n" + "\n".join(missing))

    validate_manifest(inputs["guarded_manifest"], "complete", "Guarded poisoning")
    validate_manifest(inputs["drift_manifest"], "complete", "Clean drift")
    validate_manifest(inputs["tq_manifest"], "complete", "TQ-EMA v1")
    validate_manifest(inputs["tq_v2_manifest"], "validation_failed", "TQ-EMA v2")
    validate_manifest(inputs["quantile_manifest"], "validation_failed", "Quantile")
    tq_v2_failure = validate_stopped_run(inputs["tq_v2_failure"], "TQ-EMA v2")
    quantile_failure = validate_stopped_run(inputs["quantile_failure"], "Quantile")

    attack_summary = pd.read_csv(inputs["attack_v2_summary"])
    guarded_summary = pd.read_csv(inputs["guarded_summary"])
    guarded_tradeoff = pd.read_csv(inputs["guarded_tradeoff"])
    drift_summary = pd.read_csv(inputs["drift_summary"])
    drift_subject_fold = pd.read_csv(inputs["drift_subject_fold"])
    drift_checkpoints = pd.read_csv(inputs["drift_checkpoints"])
    tq_summary = pd.read_csv(inputs["tq_summary"])
    tq_by_subject = pd.read_csv(inputs["tq_by_subject"])

    check_lambda_zero_sanity(guarded_tradeoff)
    poisoning = build_poisoning_plot_data(attack_summary, guarded_summary)

    baseline_metrics = ["late_FRR", "late_FAR", "HTER"]
    base_left = drift_summary[
        drift_summary["policy_id"].isin(["frozen", "blind", "guarded_0.25", "oracle_all"])
    ][["scenario", "D", "policy_id"] + baseline_metrics]
    base_right = tq_summary[
        tq_summary["policy_id"].isin(["frozen", "blind", "guarded_0.25", "oracle_all"])
    ][["scenario", "D", "policy_id"] + baseline_metrics]
    paired_baselines = base_left.merge(
        base_right, on=["scenario", "D", "policy_id"],
        suffixes=("_drift", "_tq"), validate="one_to_one",
    )
    for metric in baseline_metrics:
        if not np.allclose(
            paired_baselines[f"{metric}_drift"], paired_baselines[f"{metric}_tq"],
            atol=1e-9, rtol=0.0,
        ):
            raise AssertionError(f"Clean-drift baseline mismatch for {metric}")

    clean_drift = pd.concat([
        drift_summary[
            drift_summary["policy_id"].isin(["frozen", "blind", "guarded_0.25", "oracle_all"])
        ],
        tq_summary[tq_summary["policy_id"] == "tq_ema"],
    ], ignore_index=True)
    clean_columns = [
        "scenario", "D", "policy_id", "method", "late_FRR", "late_FAR", "HTER",
        "GUR", "mean_delta", "threshold_delta", "adaptation_gain", "hter_gain",
    ]
    clean_drift = clean_drift[clean_columns].sort_values(["D", "policy_id"])

    tradeoff_subjects = tq_by_subject[
        (tq_by_subject["scenario"] == "claimant_only")
        & np.isclose(tq_by_subject["D"], 2.0)
        & tq_by_subject["policy_id"].isin(DRIFT_POLICIES)
    ].copy()
    observed_policies = set(tradeoff_subjects["policy_id"])
    if observed_policies != set(DRIFT_POLICIES):
        raise AssertionError(f"Trade-off policies mismatch: {sorted(observed_policies)}")
    tradeoff = build_tradeoff_plot_data(
        tradeoff_subjects, args.bootstrap_replicates, args.seed
    )
    trajectory = build_selection_trajectory_data(
        drift_checkpoints, drift_subject_fold,
        args.bootstrap_replicates, args.seed + 101,
    )

    lambda_sweep = guarded_tradeoff[
        guarded_tradeoff["policy_id"].str.startswith("guarded_")
    ].copy().sort_values(["strategy", "K", "lambda_value"])
    summary_table = build_summary_table()

    experiment_inventory = pd.DataFrame([
        {"Experiment": "Attack v2", "Status": "complete", "Outer evaluation": "completed",
         "Role": "Frozen versus Blind vulnerability"},
        {"Experiment": "Guarded poisoning", "Status": "complete", "Outer evaluation": "completed",
         "Role": "Guarded lambda sweep; lambda=0.25 final security baseline"},
        {"Experiment": "Clean drift and Oracle-all", "Status": "complete", "Outer evaluation": "exploratory reuse",
         "Role": "Drift trade-off and selection-bias diagnostic"},
        {"Experiment": "TQ-EMA v1", "Status": "complete", "Outer evaluation": "exploratory reuse",
         "Role": "Recovery attempt; primary late-FRR criterion failed"},
        {"Experiment": "TQ-EMA v2", "Status": "validation_failed", "Outer evaluation": "not loaded",
         "Role": f"Stopped after failed folds {tq_v2_failure['failed_folds']}"},
        {"Experiment": "Adaptive Quantile", "Status": "validation_failed", "Outer evaluation": "not loaded",
         "Role": f"Stopped after failed folds {quantile_failure['failed_folds']}"},
    ])

    exclusions: list[pd.DataFrame] = []
    for experiment, key in [
        ("Guarded poisoning", "guarded_exclusions"),
        ("Clean drift and Oracle-all", "drift_exclusions"),
        ("TQ-EMA v1", "tq_exclusions"),
        ("TQ-EMA v2", "tq_v2_exclusions"),
        ("Adaptive Quantile", "quantile_exclusions"),
    ]:
        frame = pd.read_csv(inputs[key])
        frame.insert(0, "experiment", experiment)
        exclusions.append(frame)
    combined_exclusions = pd.concat(exclusions, ignore_index=True, sort=False)

    poisoning.to_csv(output_dir / "paper3_final_poisoning_plot_data.csv", index=False)
    lambda_sweep.to_csv(output_dir / "paper3_final_lambda_sweep.csv", index=False)
    clean_drift.to_csv(output_dir / "paper3_final_clean_drift.csv", index=False)
    tradeoff.to_csv(output_dir / "paper3_final_tradeoff_plot_data.csv", index=False)
    trajectory.to_csv(output_dir / "paper3_final_selection_bias_plot_data.csv", index=False)
    summary_table.to_csv(output_dir / "paper3_final_summary_table.csv", index=False)
    save_table_markdown(summary_table, output_dir / "paper3_final_summary_table.md")
    experiment_inventory.to_csv(output_dir / "paper3_final_experiment_inventory.csv", index=False)
    combined_exclusions.to_csv(output_dir / "paper3_final_exclusions.csv", index=False)

    checklist = {
        "status": "paper3_hmog_experiments_frozen",
        "freeze_tag": FREEZE_TAG,
        "hypotheses_and_endpoints_frozen": True,
        "prospective_confirmatory_status": False,
        "cohort_and_exclusions_frozen": True,
        "attack_budgets": list(EXPECTED_BUDGETS),
        "attacks": list(EXPECTED_ATTACKS),
        "primary_security_display": "Boundary attack at K=8; post-poison ASR and change from K=0",
        "primary_drift_display": "Claimant-only D=2 late FRR gain versus Frozen",
        "drift_security_constraints_pp": {"max_far_increase": 1.0, "max_hter_degradation": 0.5},
        "asr_practical_threshold": None,
        "asr_threshold_reason": "No retrospective universal cutoff added; report percentage-point effects.",
        "fold_intervals": "descriptive only",
        "clean_drift_uncertainty": "paired subject bootstrap after averaging subjects across available folds",
        "complete_case_sensitivity": "99 subjects with all five folds",
        "multiplicity": "no new hypothesis tests; secondary contrasts labeled exploratory",
        "paper1_paper2_primary_facts_verified": False,
        "paper1_paper2_note": "Exact inherited facts still require checking against primary manuscripts before submission.",
    }
    (output_dir / "paper3_final_checklist.json").write_text(
        json.dumps(checklist, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    configure_matplotlib()
    plot_poisoning(poisoning, figure_dir)
    plot_tradeoff(tradeoff, figure_dir)
    plot_selection_bias(trajectory, figure_dir)

    config = {
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "freeze_tag": FREEZE_TAG,
        "bootstrap_replicates": args.bootstrap_replicates,
        "seed": args.seed,
        "read_only_aggregation": True,
        "retraining": False,
        "rescoring": False,
        "tuning": False,
    }
    (output_dir / "config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    output_hashes = {
        str(path.relative_to(output_dir)): sha256(path)
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    manifest = {
        "status": "complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision": git_revision(source_dir),
        "freeze_tag": FREEZE_TAG,
        "python": sys.version,
        "platform": platform.platform(),
        "script_hash": sha256(Path(__file__).resolve()),
        "input_hashes": {
            str(path.relative_to(source_dir)): sha256(path)
            for path in inputs.values()
        },
        "output_hashes": output_hashes,
        "checks": {
            "attack_v2_guarded_baselines_match": True,
            "guarded_lambda_zero_matches_blind": True,
            "clean_drift_baselines_match_tq_v1": True,
            "tq_v2_outer_test_loaded": False,
            "quantile_outer_test_loaded": False,
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=4242)
    args = parser.parse_args()
    if args.bootstrap_replicates < 100:
        parser.error("--bootstrap-replicates must be at least 100")
    return args


if __name__ == "__main__":
    destination = run(parse_args())
    print(f"Saved frozen Paper 3 final analysis: {destination}")
