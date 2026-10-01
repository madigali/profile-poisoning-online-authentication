#!/usr/bin/env python3
"""
paper3_cache_scores.py

Create a reusable cache for Paper 3 from the *canonical* Paper 2 pipeline
(hmog_revised_experiment.py).

Why this exists
---------------
The old cache_probas/ directory was produced by an older experimental protocol.
Paper 3 should instead reuse the final leakage-resistant Paper 2 protocol:
session-disjoint fit/validation/test partitions, train-only scaling, the final
LSTM architecture, validation-only threshold calibration, and the same
synthetic drift function.

This script performs the expensive LSTM training once per fold, then saves:
  - validation scores;
  - clean scaled validation/test sequences;
  - test labels and chronological metadata;
  - model checkpoints;
  - test scores for each requested drift level;
  - a verification CSV reproducing the Paper 2 frozen-vs-EMA operating points.

Later Paper 3 attack/defense experiments can run from this cache without
retraining the LSTM.

Place this file next to:
    hmog_revised_experiment.py

Example:
    /opt/anaconda3/bin/python3 paper3_cache_scores.py

Optional:
    /opt/anaconda3/bin/python3 paper3_cache_scores.py \
        --dataset-cache revised_results/hmog_sequences_100.npz \
        --output-dir paper3_cache
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler

import hmog_revised_experiment as core


def save_scaler(path: Path, scaler: StandardScaler) -> None:
    np.savez_compressed(
        path,
        mean_=scaler.mean_.astype(np.float64),
        scale_=scaler.scale_.astype(np.float64),
        var_=scaler.var_.astype(np.float64),
        n_features_in_=np.asarray([scaler.n_features_in_], dtype=np.int64),
    )


def run(args: argparse.Namespace) -> None:
    # Important: seed once, before the fold loop, exactly like the canonical run().
    core.seed_everything()
    device = core.choose_device()

    data_dir = Path(args.data_dir).expanduser()
    dataset_cache = Path(args.dataset_cache)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("PAPER 3 CACHE FROM CANONICAL PAPER 2 PIPELINE")
    print("=" * 72)
    print(f"device:        {device}")
    print(f"dataset cache: {dataset_cache}")
    print(f"output dir:    {output_dir}")
    print(f"drift levels:  {tuple(args.drift_levels)}")

    data = core.load_or_build_dataset(
        data_dir=data_dir,
        max_subjects=args.max_subjects,
        cache_path=dataset_cache,
        rebuild=args.rebuild_dataset_cache,
    )

    X = data["X"]
    y = data["y"]
    session = data["session"]
    within = data["within_session"]
    subject_names = data.get("subject_names", np.asarray([], dtype=str))

    n_subjects = len(np.unique(y))
    n_features = X.shape[-1]

    print(
        f"dataset: X={X.shape}, subjects={n_subjects}, "
        f"unique session numbers={len(np.unique(session))}"
    )

    verification_rows: list[dict[str, float]] = []
    fold_meta: list[dict] = []

    for fold in range(core.N_FOLDS):
        fold_number = fold + 1
        print("\n" + "-" * 72)
        print(f"Fold {fold_number}/{core.N_FOLDS}")
        print("-" * 72)

        fit_mask, val_mask, test_mask = core.fold_masks(session, fold)

        for name, mask in (
            ("fit", fit_mask),
            ("validation", val_mask),
            ("test", test_mask),
        ):
            n_here = len(np.unique(y[mask]))
            if n_here != n_subjects:
                raise RuntimeError(
                    f"fold {fold_number}: {name} contains {n_here}/{n_subjects} subjects"
                )

        scaler = StandardScaler().fit(
            X[fit_mask].reshape(-1, n_features)
        )

        X_fit = core.scale_sequences(scaler, X[fit_mask])
        X_val = core.scale_sequences(scaler, X[val_mask])
        X_test_clean = core.scale_sequences(scaler, X[test_mask])

        y_fit = y[fit_mask]
        y_val = y[val_mask]
        y_test = y[test_mask]

        session_val = session[val_mask]
        within_val = within[val_mask]
        session_test = session[test_mask]
        within_test = within[test_mask]

        print(
            f"fit={len(X_fit)}, val={len(X_val)}, test={len(X_test_clean)}"
        )

        model, best_epoch = core.train_lstm(
            X_fit,
            y_fit,
            X_val,
            y_val,
            n_subjects,
            device,
        )

        val_scores = core.predict_lstm(model, X_val, device).astype(np.float32)

        # Save reusable base arrays. X_val and X_test_clean are included deliberately:
        # they let us add more drift seeds and extract LSTM embeddings later without
        # retraining the model.
        base_path = output_dir / f"fold{fold_number}_base.npz"
        np.savez_compressed(
            base_path,
            X_val=X_val.astype(np.float32),
            y_val=y_val.astype(np.int64),
            session_val=session_val.astype(np.int64),
            within_val=within_val.astype(np.int64),
            val_scores=val_scores,
            X_test_clean=X_test_clean.astype(np.float32),
            y_test=y_test.astype(np.int64),
            session_test=session_test.astype(np.int64),
            within_test=within_test.astype(np.int64),
            subject_names=subject_names,
        )

        scaler_path = output_dir / f"fold{fold_number}_scaler.npz"
        save_scaler(scaler_path, scaler)

        model_path = output_dir / f"fold{fold_number}_model.pt"
        torch.save(
            {
                "state_dict": model.state_dict(),
                "n_classes": n_subjects,
                "n_features": n_features,
                "best_epoch": best_epoch,
                "paper2_seed": core.SEED,
                "lstm_hidden": core.LSTM_HIDDEN,
                "lstm_layers": core.LSTM_LAYERS,
                "dropout": core.DROPOUT,
            },
            model_path,
        )

        fold_meta.append(
            {
                "fold": fold_number,
                "best_epoch": int(best_epoch),
                "fit_n": int(fit_mask.sum()),
                "validation_n": int(val_mask.sum()),
                "test_n": int(test_mask.sum()),
                "fit_sessions": sorted(map(int, np.unique(session[fit_mask]))),
                "validation_sessions": sorted(map(int, np.unique(session[val_mask]))),
                "test_sessions": sorted(map(int, np.unique(session[test_mask]))),
                "base_file": base_path.name,
                "model_file": model_path.name,
                "scaler_file": scaler_path.name,
            }
        )

        for drift in args.drift_levels:
            drift = float(drift)

            # Match the canonical Paper 2 drift seed exactly.
            X_test = core.inject_drift(
                X_test_clean,
                y_test,
                session_test,
                within_test,
                magnitude=drift,
                seed=core.SEED + fold,
            )

            test_scores = core.predict_lstm(
                model, X_test, device
            ).astype(np.float32)

            score_path = output_dir / f"fold{fold_number}_D{drift:.1f}.npz"
            np.savez_compressed(
                score_path,
                test_scores=test_scores,
                y_test=y_test.astype(np.int64),
                session_test=session_test.astype(np.int64),
                within_test=within_test.astype(np.int64),
                drift_l2=np.asarray([drift], dtype=np.float32),
                drift_seed=np.asarray([core.SEED + fold], dtype=np.int64),
            )

            # Verification against the canonical Paper 2 operating-point evaluation.
            operating = core.evaluate_operating_points(
                val_scores,
                test_scores,
                y_val,
                y_test,
                session_test,
                within_test,
                fold,
                drift,
            )

            lstm_eer, _ = core.macro_eer(test_scores, y_test)

            row = {
                "fold": fold_number,
                "drift_l2": drift,
                "LSTM_EER": 100.0 * lstm_eer,
                **operating,
            }
            verification_rows.append(row)

            print(
                f"D={drift:.1f} | "
                f"EER={100*lstm_eer:.2f}% | "
                f"frozen HTER={operating['static_HTER']:.2f}% | "
                f"EMA HTER={operating['adaptive_HTER']:.2f}%"
            )

        del model
        if device.type == "mps":
            torch.mps.empty_cache()
        elif device.type == "cuda":
            torch.cuda.empty_cache()

    verification = pd.DataFrame(verification_rows)
    verification_path = output_dir / "paper2_verification_by_fold.csv"
    verification.to_csv(verification_path, index=False)

    summary_columns = [
        "LSTM_EER",
        "static_FAR",
        "static_FRR",
        "static_HTER",
        "adaptive_FAR",
        "adaptive_FRR",
        "adaptive_HTER",
    ]
    summary = (
        verification.groupby("drift_l2")[summary_columns]
        .agg(["mean", "std"])
        .round(4)
    )
    summary_path = output_dir / "paper2_verification_summary.csv"
    summary.to_csv(summary_path)

    metadata = {
        "purpose": "Paper 3 reusable cache built from canonical Paper 2 protocol",
        "canonical_module": "hmog_revised_experiment.py",
        "seed": core.SEED,
        "n_folds": core.N_FOLDS,
        "n_subjects": int(n_subjects),
        "n_sequences": int(len(X)),
        "sequence_length": int(core.SEQ_LEN),
        "sequence_step": int(core.SEQ_STEP),
        "window_size": int(core.WINDOW_SIZE),
        "windows_per_session": int(core.WINDOWS_PER_SESSION),
        "window_offset": int(core.WINDOW_OFFSET),
        "lstm_hidden": int(core.LSTM_HIDDEN),
        "lstm_layers": int(core.LSTM_LAYERS),
        "dropout": float(core.DROPOUT),
        "agent_alpha": float(core.AGENT_ALPHA),
        "agent_min_sigma": float(core.AGENT_MIN_SIGMA),
        "drift_levels_l2": [float(x) for x in args.drift_levels],
        "stream_repeats_for_verification": int(core.STREAM_REPEATS),
        "dataset_cache": str(dataset_cache),
        "folds": fold_meta,
    }
    with open(
        output_dir / "paper3_cache_metadata.json",
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(metadata, handle, indent=2)

    print("\n" + "=" * 72)
    print("VERIFICATION SUMMARY")
    print("=" * 72)
    print(summary)
    print("\nExpected Paper 2 reference means (approximately):")
    print("  D=0: frozen HTER ~23.19%, EMA HTER ~24.53%")
    print("  D=1: frozen HTER ~23.63%, EMA HTER ~25.02%")
    print("  D=2: frozen HTER ~24.89%, EMA HTER ~26.39%")
    print("\nIf your reproduced means are materially different, STOP before Paper 3 attacks.")
    print(f"\nSaved cache to: {output_dir.resolve()}")
    print("Next step after verification: paper3_poisoning_attack.py")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        default="~/Downloads/public_dataset",
        help="Used only if the canonical dataset cache must be rebuilt.",
    )
    parser.add_argument(
        "--dataset-cache",
        default="revised_results/hmog_sequences_100.npz",
        help="Canonical Paper 2 sequence cache.",
    )
    parser.add_argument(
        "--output-dir",
        default="paper3_cache",
    )
    parser.add_argument(
        "--max-subjects",
        type=int,
        default=core.MAX_SUBJECTS,
    )
    parser.add_argument(
        "--drift-levels",
        type=float,
        nargs="+",
        default=list(core.DRIFT_LEVELS),
    )
    parser.add_argument(
        "--rebuild-dataset-cache",
        action="store_true",
        help="Rebuild HMOG sequences from raw zip files. Usually leave this OFF.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    run(parse_args())
