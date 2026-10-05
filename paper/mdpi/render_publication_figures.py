#!/usr/bin/env python3
"""Presentation-only renderer for four Paper 3 figures.

The script reads frozen plot-data/state tables. It does not train, score,
adapt, bootstrap, or recompute experimental endpoints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


COLORS = {
    "frozen": "#4D4D4D",
    "blind": "#D55E00",
    "guarded_0.25": "#0072B2",
    "oracle_all": "#009E73",
}
MARKERS = {"frozen": "o", "blind": "s", "guarded_0.25": "^", "oracle_all": "D"}
LABELS = {
    "frozen": "Frozen",
    "blind": "Blind EMA",
    "guarded_0.25": "Guarded EMA (λ=0.25)",
    "oracle_all": "Oracle-all EMA",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def configure() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10.5,
        "legend.fontsize": 9.5,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
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


def save(fig: plt.Figure, target: Path) -> None:
    fig.savefig(target, facecolor="white")
    plt.close(fig)


def figure1(root: Path, out: Path) -> tuple[Path, Path]:
    source = root / "results/paper3_final_analysis_20261002_v2/paper3_final_poisoning_plot_data.csv"
    original = root / "results/paper3_final_analysis_20261002_v2/figures/figure1_poisoning_asr.pdf"
    data = pd.read_csv(source)
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.15), sharex=True, sharey=True)
    for axis, strategy, panel in zip(axes, ["random", "boundary"], ["a", "b"]):
        group = data[data["strategy"] == strategy]
        for policy in ("frozen", "blind", "guarded_0.25"):
            line = group[group["policy_id"] == policy].sort_values("K")
            x = line["K"].to_numpy(float)
            mean = line["mean"].to_numpy(float)
            low = line["ci95_low"].to_numpy(float)
            high = line["ci95_high"].to_numpy(float)
            axis.plot(x, mean, color=COLORS[policy], marker=MARKERS[policy],
                      markersize=5.5, label=LABELS[policy])
            axis.fill_between(x, low, high, color=COLORS[policy], alpha=0.12)
        axis.set_title(f"({panel}) {strategy.capitalize()} attack")
        axis.set_xlabel("Presented poisoning attempts K")
        axis.set_xticks([0, 1, 2, 4, 8])
    axes[0].set_ylabel("Post-poison attack success rate (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle("Profile poisoning under nested attack budgets", y=0.98, fontsize=12)
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.915),
               ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.80))
    save(fig, out / "figure1_poisoning_asr.pdf")
    return source, original


def figure4(root: Path, out: Path) -> tuple[Path, Path]:
    source = root / "results/paper3_final_analysis_20261002_v2/paper3_final_selection_bias_plot_data.csv"
    original = root / "results/paper3_final_analysis_20261002_v2/figures/figure3_selection_bias_mechanism.pdf"
    data = pd.read_csv(source)
    metrics = [
        ("mean_delta", "Change in profile mean", "Score change"),
        ("threshold_delta", "Change in authentication threshold", "Score change"),
        ("update_rate", "Genuine update rate", "Update rate (%)"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.2), sharex=True)
    for axis, (metric, title, ylabel), panel in zip(axes, metrics, ["a", "b", "c"]):
        group = data[data["metric"] == metric]
        for policy in ("guarded_0.25", "oracle_all"):
            line = group[group["policy_id"] == policy].sort_values("checkpoint")
            x = line["session_checkpoint"].to_numpy(float)
            estimate = line["estimate"].to_numpy(float)
            low = line["ci95_low"].to_numpy(float)
            high = line["ci95_high"].to_numpy(float)
            axis.plot(x, estimate, color=COLORS[policy], marker=MARKERS[policy],
                      markersize=5.5, label=LABELS[policy])
            axis.fill_between(x, low, high, color=COLORS[policy], alpha=0.13)
        if metric != "update_rate":
            axis.axhline(0.0, color="#777777", linewidth=0.9, alpha=0.55)
        axis.set_title(f"({panel}) {title}")
        axis.set_xlabel("Session checkpoint")
        axis.set_ylabel(ylabel)
        axis.set_xticks([1, 2, 3, 4, 5])
    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle("Update eligibility changes profile trajectories\nunder the imposed feature shift",
                 y=0.995, fontsize=12)
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.865),
               ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.73))
    save(fig, out / "figure4_selection_bias_mechanism.pdf")
    return source, original


def figure_s2(root: Path, out: Path) -> tuple[Path, Path]:
    source = root / "results/paper3_operating_point_sensitivity_20261004_v1/eligibility_summary.csv"
    original = root / "results/paper3_operating_point_sensitivity_20261004_v1/figures/boundary_feasibility.pdf"
    data = pd.read_csv(source)
    order = ["reference", "far_5pct", "far_1pct"]
    labels = ["Reference", "Nominal 5%", "Nominal 1%"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True, sharey=True)
    for axis, dataset in zip(axes, ("HMOG", "McGill")):
        selected = data[(data["dataset"] == dataset) & (data["strategy"] == "boundary")]
        for condition, label in zip(order, labels):
            part = selected[selected["condition"] == condition].sort_values("K")
            axis.plot(part["K"], 100 * part["eligible_path_fraction"],
                      marker="o", label=label)
        axis.set_title(dataset)
        axis.set_xlabel("Presented poisoning attempts K")
        axis.set_xticks([1, 2, 4, 8])
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Feasible planned paths (%)")
    axes[1].legend(frameon=False)
    save(fig, out / "figureS2_boundary_feasibility.pdf")
    return source, original


def figure_s6(root: Path, out: Path) -> tuple[Path, Path]:
    source = root / "results/paper3_external_mcgill_20261003_v1/temporal_checkpoints.csv"
    original = root / "results/paper3_external_mcgill_20261003_v1/figures/external_selection_bias_trajectory.pdf"
    data = pd.read_csv(source)
    trajectory = data.groupby(["method", "unit"], as_index=False).agg(
        mean=("mean", "mean"),
        threshold=("threshold", "mean"),
        frr=("checkpoint_FRR", "mean"),
        update_rate=("update_event", "mean"),
    )
    colors = {
        "Frozen": "#4C566A",
        "Blind EMA": "#BF616A",
        "Guarded EMA": "#2A9D8F",
        "Oracle-all-genuine": "#5E3C99",
    }
    methods = ["Frozen", "Guarded EMA", "Oracle-all-genuine"]
    fields = (
        ("mean", "Profile mean", 1.0),
        ("threshold", "Unclipped authentication threshold", 1.0),
        ("frr", "Checkpoint FRR", 1.0),
        ("update_rate", "Update rate", 100.0),
    )
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.3), sharex=True)
    for axis, (field, title, scale) in zip(axes.flat, fields):
        for method in methods:
            line = trajectory[trajectory["method"] == method]
            axis.plot(line["unit"], scale * line[field], label=method, color=colors[method])
        axis.set_title(title)
        axis.grid(alpha=0.25)
    axes[1, 0].set_xlabel("Temporal unit")
    axes[1, 1].set_xlabel("Temporal unit")
    axes[1, 0].set_ylabel("Rate (%)")
    axes[1, 1].set_ylabel("Rate (%)")
    axes[0, 1].legend(frameon=False, fontsize=9)
    fig.tight_layout()
    save(fig, out / "figureS6_external_selection_bias_trajectory.pdf")
    return source, original


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    configure()
    jobs = {
        "figure1_poisoning_asr.pdf": figure1(root, out),
        "figure4_selection_bias_mechanism.pdf": figure4(root, out),
        "figureS2_boundary_feasibility.pdf": figure_s2(root, out),
        "figureS6_external_selection_bias_trajectory.pdf": figure_s6(root, out),
    }
    registry = []
    changes = {
        "figure1_poisoning_asr.pdf": "x-axis label only",
        "figure4_selection_bias_mechanism.pdf": "title wording, font sizing, and legend spacing only",
        "figureS2_boundary_feasibility.pdf": "x-axis label and ticks only",
        "figureS6_external_selection_bias_trajectory.pdf": "threshold-panel title, font sizing, and layout only",
    }
    for name, (numeric_source, original) in jobs.items():
        publication = out / name
        registry.append({
            "original_artifact": str(original.relative_to(root)),
            "original_sha256": digest(original),
            "publication_copy": str(publication),
            "publication_sha256": digest(publication),
            "presentation_change": changes[name],
            "numeric_source": str(numeric_source.relative_to(root)),
            "numeric_source_sha256": digest(numeric_source),
            "scientific_values_recomputed": False,
        })
    (out / "artwork_registry.json").write_text(
        json.dumps(registry, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
