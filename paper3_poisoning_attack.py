#!/usr/bin/env python3
"""
paper3_poisoning_attack.py

Paper 3 — Attack-only screening experiment.

Purpose
-------
Before implementing a defense, test whether the canonical Paper 2 EMA adaptation
creates a measurable profile-poisoning surface.

Uses ONLY the fixed cache produced by paper3_cache_scores.py.
No LSTM retraining is performed.

Initial scope:
  * drift D=0 only;
  * random zero-effort impostor stream;
  * high-score targeted impostor stream;
  * identical attack streams for all compared decision rules.

Compared rules:
  1) Frozen threshold
  2) Label-blind EMA (Paper 2 behavior: every accepted sample updates)
  3) Oracle-gated EMA (diagnostic control only: accepted impostors do NOT update)

The oracle is not a deployable method. It isolates how much degradation is due
specifically to malicious updates rather than ordinary genuine-user adaptation.

Outputs:
  paper3_attack_v1_by_fold.csv
  paper3_attack_v1_summary.csv
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

import hmog_revised_experiment as core


DEFAULT_REPEATS = 100
DEFAULT_TARGET_TOP_FRACTION = 0.10


def load_fold(cache_dir: Path, fold: int, drift: float = 0.0):
    base = np.load(cache_dir / f"fold{fold}_base.npz")
    scores = np.load(cache_dir / f"fold{fold}_D{drift:.1f}.npz")
    return {
        "val_scores": base["val_scores"],
        "y_val": base["y_val"],
        "test_scores": scores["test_scores"],
        "y_test": scores["y_test"],
        "session_test": scores["session_test"],
        "within_test": scores["within_test"],
    }


def accepted_without_update(agent: core.AdaptiveEMA, score: float) -> bool:
    return score >= agent.threshold


def choose_attack_indices(
    strategy: str,
    impostor_pool: np.ndarray,
    victim_scores: np.ndarray,
    n_attacks: int,
    rng: np.random.Generator,
    top_fraction: float,
) -> np.ndarray:
    if strategy == "random":
        return rng.choice(impostor_pool, size=n_attacks, replace=False)

    if strategy == "high_score":
        # Attacker chooses from the highest victim-score impostors.
        # We sample from the top fraction rather than always taking the exact
        # same top-k so that repeated trials quantify variability.
        ranked = impostor_pool[np.argsort(victim_scores[impostor_pool])[::-1]]
        pool_size = max(n_attacks, int(math.ceil(len(ranked) * top_fraction)))
        candidate_pool = ranked[:pool_size]
        return rng.choice(candidate_pool, size=n_attacks, replace=False)

    raise ValueError(f"unknown strategy: {strategy}")


def rate(x):
    return float(np.mean(x)) if len(x) else float("nan")


def evaluate_one_stream(
    sid: int,
    tau0: float,
    enrollment: np.ndarray,
    genuine_idx: np.ndarray,
    attack_idx: np.ndarray,
    test_scores: np.ndarray,
):
    frozen_attack = []
    frozen_genuine_reject = []

    blind_attack = []
    blind_genuine_reject = []

    oracle_attack = []
    oracle_genuine_reject = []

    blind_thresholds = [tau0]
    oracle_thresholds = [tau0]

    blind = core.AdaptiveEMA.from_enrollment(enrollment, tau0)
    oracle = core.AdaptiveEMA.from_enrollment(enrollment, tau0)

    for gi, ai in zip(genuine_idx, attack_idx):
        gs = float(test_scores[gi, sid])
        ms = float(test_scores[ai, sid])

        # Frozen
        frozen_genuine_reject.append(gs < tau0)
        frozen_attack.append(ms >= tau0)

        # Label-blind Paper 2 EMA:
        # genuine decision may update; malicious accepted decision may also update.
        blind_genuine_reject.append(not blind.decide(gs))
        blind_attack.append(blind.decide(ms))
        blind_thresholds.append(blind.threshold)

        # Oracle diagnostic:
        # genuine samples behave exactly like EMA;
        # malicious samples are scored but NEVER allowed to update.
        oracle_genuine_reject.append(not oracle.decide(gs))
        oa = accepted_without_update(oracle, ms)
        oracle_attack.append(oa)
        oracle_thresholds.append(oracle.threshold)

    frozen_attack = np.asarray(frozen_attack, dtype=bool)
    blind_attack = np.asarray(blind_attack, dtype=bool)
    oracle_attack = np.asarray(oracle_attack, dtype=bool)

    frozen_genuine_reject = np.asarray(frozen_genuine_reject, dtype=bool)
    blind_genuine_reject = np.asarray(blind_genuine_reject, dtype=bool)
    oracle_genuine_reject = np.asarray(oracle_genuine_reject, dtype=bool)

    n = len(attack_idx)
    split = max(1, n // 2)

    def attack_stats(decisions):
        early = rate(decisions[:split])
        late = rate(decisions[split:]) if split < n else early
        return {
            "ASR": rate(decisions),
            "ASR_early": early,
            "ASR_late": late,
            "dASR_late_early": late - early,
        }

    out = {}

    for name, attack_decisions, genuine_rejects in [
        ("frozen", frozen_attack, frozen_genuine_reject),
        ("ema_blind", blind_attack, blind_genuine_reject),
        ("ema_oracle", oracle_attack, oracle_genuine_reject),
    ]:
        stats = attack_stats(attack_decisions)
        out[f"{name}_ASR"] = stats["ASR"]
        out[f"{name}_ASR_early"] = stats["ASR_early"]
        out[f"{name}_ASR_late"] = stats["ASR_late"]
        out[f"{name}_dASR"] = stats["dASR_late_early"]
        out[f"{name}_FRR"] = rate(genuine_rejects)

    # For label-blind EMA, every accepted malicious attempt is also a malicious update.
    out["ema_blind_MUR"] = rate(blind_attack)

    # Oracle explicitly blocks malicious updates.
    out["ema_oracle_MUR"] = 0.0

    # Positive value = threshold moved downward from initial calibration point.
    out["ema_blind_threshold_drop"] = tau0 - float(blind_thresholds[-1])
    out["ema_oracle_threshold_drop"] = tau0 - float(oracle_thresholds[-1])

    # Poisoning-specific paired effects.
    out["blind_minus_frozen_ASR"] = out["ema_blind_ASR"] - out["frozen_ASR"]
    out["blind_minus_oracle_ASR"] = out["ema_blind_ASR"] - out["ema_oracle_ASR"]
    out["blind_minus_oracle_FRR"] = out["ema_blind_FRR"] - out["ema_oracle_FRR"]

    return out


def run(args):
    cache_dir = Path(args.cache_dir)

    rows = []

    for fold in range(1, core.N_FOLDS + 1):
        data = load_fold(cache_dir, fold, drift=0.0)
        val_scores = data["val_scores"]
        y_val = data["y_val"]
        test_scores = data["test_scores"]
        y_test = data["y_test"]
        session_test = data["session_test"]
        within_test = data["within_test"]

        print(f"\nFold {fold}/{core.N_FOLDS}")

        for strategy in ("random", "high_score"):
            subject_rows = []

            for sid in range(test_scores.shape[1]):
                enrollment = val_scores[y_val == sid, sid]
                validation_impostor = val_scores[y_val != sid, sid]
                genuine_idx = core.chronology_order(
                    session_test,
                    within_test,
                    np.flatnonzero(y_test == sid),
                )
                impostor_pool = np.flatnonzero(y_test != sid)

                if len(enrollment) < 2 or len(genuine_idx) < 2:
                    continue
                if len(impostor_pool) < len(genuine_idx):
                    continue

                _, tau0 = core.eer_from_scores(enrollment, validation_impostor)

                for repeat in range(args.repeats):
                    rng = np.random.default_rng(
                        args.seed
                        + fold * 1_000_000
                        + sid * 10_000
                        + repeat * 10
                        + (0 if strategy == "random" else 1)
                    )

                    attack_idx = choose_attack_indices(
                        strategy=strategy,
                        impostor_pool=impostor_pool,
                        victim_scores=test_scores[:, sid],
                        n_attacks=len(genuine_idx),
                        rng=rng,
                        top_fraction=args.target_top_fraction,
                    )

                    metrics = evaluate_one_stream(
                        sid=sid,
                        tau0=tau0,
                        enrollment=enrollment,
                        genuine_idx=genuine_idx,
                        attack_idx=attack_idx,
                        test_scores=test_scores,
                    )

                    subject_rows.append(
                        {
                            "fold": fold,
                            "strategy": strategy,
                            "sid": sid,
                            "repeat": repeat,
                            "n_genuine": len(genuine_idx),
                            "n_attacks": len(attack_idx),
                            "tau0": tau0,
                            **metrics,
                        }
                    )

            df_subject = pd.DataFrame(subject_rows)
            if df_subject.empty:
                continue

            # Average first over repeat+subject observations within the fold.
            numeric = df_subject.select_dtypes(include=[np.number]).columns
            means = df_subject[numeric].mean()

            row = {
                "fold": fold,
                "strategy": strategy,
                **{k: float(means[k]) for k in means.index
                   if k not in {"fold", "sid", "repeat"}},
            }
            rows.append(row)

            print(
                f"  {strategy:10s} | "
                f"Frozen ASR={100*row['frozen_ASR']:.2f}% | "
                f"Blind EMA ASR={100*row['ema_blind_ASR']:.2f}% | "
                f"Oracle EMA ASR={100*row['ema_oracle_ASR']:.2f}% | "
                f"Blind-Oracle={100*row['blind_minus_oracle_ASR']:+.2f} pp | "
                f"threshold drop={row['ema_blind_threshold_drop']:+.4f}"
            )

    by_fold = pd.DataFrame(rows)

    # Convert rates to percentages in the exported human-readable tables.
    percentage_cols = [
        c for c in by_fold.columns
        if (
            c.endswith("_ASR")
            or c.endswith("_ASR_early")
            or c.endswith("_ASR_late")
            or c.endswith("_dASR")
            or c.endswith("_FRR")
            or c.endswith("_MUR")
        )
        or c in {
            "blind_minus_frozen_ASR",
            "blind_minus_oracle_ASR",
            "blind_minus_oracle_FRR",
        }
    ]

    export = by_fold.copy()
    for c in percentage_cols:
        if c in export:
            export[c] = 100.0 * export[c]

    export.to_csv(args.output_by_fold, index=False)

    summary_rows = []
    for strategy, g in export.groupby("strategy"):
        for c in [
            "frozen_ASR",
            "ema_blind_ASR",
            "ema_oracle_ASR",
            "ema_blind_FRR",
            "ema_oracle_FRR",
            "ema_blind_MUR",
            "blind_minus_frozen_ASR",
            "blind_minus_oracle_ASR",
            "ema_blind_dASR",
            "ema_blind_threshold_drop",
            "ema_oracle_threshold_drop",
        ]:
            if c not in g:
                continue
            summary_rows.append(
                {
                    "strategy": strategy,
                    "metric": c,
                    "mean": float(g[c].mean()),
                    "std_across_folds": float(g[c].std(ddof=1)),
                }
            )

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(args.output_summary, index=False)

    print("\n" + "=" * 80)
    print("SUMMARY ACROSS 5 FOLDS")
    print("=" * 80)
    pivot = summary.pivot(index="metric", columns="strategy", values="mean")
    print(pivot.round(3).to_string())

    print("\nInterpretation for attack screening:")
    print("  1) blind_minus_oracle_ASR > 0 suggests malicious profile updates")
    print("     increase subsequent attack acceptance beyond genuine-only adaptation.")
    print("  2) ema_blind_dASR > 0 suggests attacks become easier later in the stream.")
    print("  3) positive ema_blind_threshold_drop means the adaptive threshold moved down.")
    print("  4) If these effects are near zero, do NOT force a poisoning-defense paper;" )
    print("     reconsider the threat model before implementing the Safe Agent.")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--cache-dir", default="paper3_cache")
    p.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    p.add_argument("--seed", type=int, default=4242)
    p.add_argument(
        "--target-top-fraction",
        type=float,
        default=DEFAULT_TARGET_TOP_FRACTION,
        help="For high_score attack, sample from the top fraction of victim-score impostors.",
    )
    p.add_argument(
        "--output-by-fold",
        default="paper3_attack_v1_by_fold.csv",
    )
    p.add_argument(
        "--output-summary",
        default="paper3_attack_v1_summary.csv",
    )
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
