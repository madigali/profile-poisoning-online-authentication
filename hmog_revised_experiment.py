"""Leakage-resistant HMOG experiments for the revised manuscript.

This script is the canonical experiment pipeline.  It deliberately replaces the
older ``hmog_*`` scripts, whose cached numbers must not be used in the paper.

Protocol highlights
-------------------
* HMOG sensor axes are columns 4--6 (zero-based slice 3:6).  Earlier scripts
  accidentally included timestamps and the session identifier.
* Windows never overlap and sequences never cross session boundaries.
* Outer folds are session-disjoint; every subject contributes sessions to every
  fold.  A second, disjoint session fold is used for validation/calibration.
* The scaler is fitted on the model-fitting partition only.
* SVM, RF and LSTM receive the same 10 x 36 sequence (classical models receive
  its flattened representation).
* The static and adaptive LSTM operating points start from the same enrollment
  profile.  Agent parameters are fixed before inspecting test results.

Run with the Anaconda Python used for the original experiments:
    /opt/anaconda3/bin/python3 hmog_revised_experiment.py
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import random
import re
import warnings
import zipfile
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import skew
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_curve
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset


SEED = 42
WINDOW_SIZE = 100
WINDOWS_PER_SESSION = 20
WINDOW_OFFSET = 500
SEQ_LEN = 10
SEQ_STEP = 10
N_FOLDS = 5
MAX_SUBJECTS = 100

LSTM_HIDDEN = 64
LSTM_LAYERS = 2
DROPOUT = 0.30
BATCH_SIZE = 256
EPOCHS = 20
PATIENCE = 4
LR = 1e-3

# Fixed a priori. alpha=0.05 has an effective memory of about 1/alpha=20
# accepted observations. Each claimant's k is derived from the validation EER
# operating point; no test score is used for threshold calibration.
AGENT_ALPHA = 0.05
AGENT_MIN_SIGMA = 1e-4
DRIFT_LEVELS = (0.0, 1.0, 2.0)
STREAM_REPEATS = 10

SESSION_RE = re.compile(r"session_(\d+)", re.IGNORECASE)


def seed_everything(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)


def choose_device() -> torch.device:
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def find_sessions(names: list[str]) -> list[tuple[int, str, str]]:
    by_dir: dict[str, dict[str, str]] = {}
    for name in names:
        base = os.path.basename(name).lower()
        if base not in {"accelerometer.csv", "gyroscope.csv"}:
            continue
        directory = os.path.dirname(name)
        by_dir.setdefault(directory, {})["acc" if base.startswith("acc") else "gyr"] = name

    sessions = []
    for directory, files in by_dir.items():
        if "acc" not in files or "gyr" not in files:
            continue
        match = SESSION_RE.search(directory)
        if match:
            sessions.append((int(match.group(1)), files["acc"], files["gyr"]))
    return sorted(sessions, key=lambda item: item[0])


def sensor_axes(frame: pd.DataFrame) -> np.ndarray:
    """Return HMOG x/y/z columns; metadata occupies columns 0, 1, 2 and 6."""
    if frame.shape[1] < 6:
        raise ValueError(f"expected at least 6 HMOG columns, got {frame.shape[1]}")
    return frame.iloc[:, 3:6].to_numpy(dtype=np.float64, copy=True)


def extract_features(window: np.ndarray) -> np.ndarray:
    out = []
    for column in window.T:
        std = float(np.std(column))
        out.extend(
            [
                float(np.mean(column)),
                std,
                float(np.min(column)),
                float(np.max(column)),
                float(np.sqrt(np.mean(column * column))),
                float(skew(column)) if std > 0 else 0.0,
            ]
        )
    return np.nan_to_num(np.asarray(out, dtype=np.float32))


def read_session(zf: zipfile.ZipFile, acc_name: str, gyr_name: str) -> np.ndarray:
    nrows = WINDOW_OFFSET + WINDOWS_PER_SESSION * WINDOW_SIZE
    with zf.open(acc_name) as handle:
        acc = pd.read_csv(handle, header=None, nrows=nrows)
    with zf.open(gyr_name) as handle:
        gyr = pd.read_csv(handle, header=None, nrows=nrows)

    # HMOG inertial streams are sampled synchronously.  We pair samples by
    # acquisition order after truncating to their common length.
    av, gv = sensor_axes(acc), sensor_axes(gyr)
    n = min(len(av), len(gv))
    if n < WINDOW_OFFSET + SEQ_LEN * WINDOW_SIZE:
        return np.empty((0, 36), dtype=np.float32)
    data = np.nan_to_num(np.hstack([av[:n], gv[:n]]))

    features = []
    start = WINDOW_OFFSET
    while start + WINDOW_SIZE <= n and len(features) < WINDOWS_PER_SESSION:
        features.append(extract_features(data[start : start + WINDOW_SIZE]))
        start += WINDOW_SIZE
    return np.asarray(features, dtype=np.float32)


def build_dataset(data_dir: Path, max_subjects: int, cache_path: Path) -> dict[str, np.ndarray]:
    zip_paths = sorted(data_dir.glob("*.zip"))[:max_subjects]
    if not zip_paths:
        raise FileNotFoundError(f"no HMOG zip files found in {data_dir}")

    sequences, labels, session_numbers, within_session = [], [], [], []
    subject_names = []
    skipped_sessions = []
    valid_sid = 0
    for source_index, zip_path in enumerate(zip_paths):
        subject_sequences, subject_sessions, subject_within = [], [], []
        with zipfile.ZipFile(zip_path) as zf:
            sessions = find_sessions(zf.namelist())
            for session_number, acc_name, gyr_name in sessions:
                try:
                    windows = read_session(zf, acc_name, gyr_name)
                except (pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as exc:
                    skipped_sessions.append(
                        {"subject": zip_path.stem, "session": session_number, "reason": type(exc).__name__}
                    )
                    continue
                for start in range(0, len(windows) - SEQ_LEN + 1, SEQ_STEP):
                    subject_sequences.append(windows[start : start + SEQ_LEN])
                    subject_sessions.append(session_number)
                    subject_within.append(start)

        present_folds = set((np.asarray(subject_sessions) - 1) % N_FOLDS)
        if present_folds != set(range(N_FOLDS)):
            skipped_sessions.append(
                {"subject": zip_path.stem, "session": None, "reason": "missing_fold_after_quality_checks"}
            )
        else:
            sequences.extend(subject_sequences)
            labels.extend([valid_sid] * len(subject_sequences))
            session_numbers.extend(subject_sessions)
            within_session.extend(subject_within)
            subject_names.append(zip_path.stem)
            valid_sid += 1

        print(f"loaded {source_index + 1:3d}/{len(zip_paths)} subjects", flush=True)

    payload = {
        "X": np.asarray(sequences, dtype=np.float32),
        "y": np.asarray(labels, dtype=np.int64),
        "session": np.asarray(session_numbers, dtype=np.int64),
        "within_session": np.asarray(within_session, dtype=np.int64),
        "subject_names": np.asarray(subject_names),
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache_path, **payload)
    with open(cache_path.with_suffix(".quality.json"), "w", encoding="utf-8") as handle:
        json.dump(skipped_sessions, handle, indent=2)
    return payload


def load_or_build_dataset(data_dir: Path, max_subjects: int, cache_path: Path, rebuild: bool) -> dict[str, np.ndarray]:
    if cache_path.exists() and not rebuild:
        with np.load(cache_path) as archive:
            payload = {key: archive[key] for key in archive.files}
        if len(np.unique(payload["y"])) > 0:
            return payload
    return build_dataset(data_dir, max_subjects, cache_path)


def fold_masks(session: np.ndarray, outer_fold: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    fold_id = (session - 1) % N_FOLDS
    test = fold_id == outer_fold
    validation = fold_id == ((outer_fold + 1) % N_FOLDS)
    fit = ~(test | validation)
    return fit, validation, test


class LSTMAuth(nn.Module):
    def __init__(self, input_size: int, n_classes: int):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=LSTM_HIDDEN,
            num_layers=LSTM_LAYERS,
            batch_first=True,
            dropout=DROPOUT,
        )
        self.norm = nn.LayerNorm(LSTM_HIDDEN)
        self.head = nn.Sequential(
            nn.Linear(LSTM_HIDDEN, 32), nn.ReLU(), nn.Dropout(DROPOUT), nn.Linear(32, n_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        sequence, _ = self.lstm(x)
        return self.head(self.norm(sequence[:, -1, :]))


def predict_lstm(model: nn.Module, X: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    outputs = []
    tensor = torch.as_tensor(X, dtype=torch.float32)
    loader = DataLoader(TensorDataset(tensor), batch_size=BATCH_SIZE * 4)
    with torch.no_grad():
        for (batch,) in loader:
            outputs.append(torch.softmax(model(batch.to(device)), dim=1).cpu().numpy())
    return np.vstack(outputs)


def train_lstm(X_fit: np.ndarray, y_fit: np.ndarray, X_val: np.ndarray, y_val: np.ndarray,
               n_classes: int, device: torch.device) -> tuple[nn.Module, int]:
    model = LSTMAuth(X_fit.shape[-1], n_classes).to(device)
    optimizer = optim.Adam(model.parameters(), lr=LR)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=0.5, patience=2)
    loss_fn = nn.CrossEntropyLoss()
    generator = torch.Generator().manual_seed(SEED)
    loader = DataLoader(
        TensorDataset(torch.as_tensor(X_fit), torch.as_tensor(y_fit)),
        batch_size=BATCH_SIZE,
        shuffle=True,
        generator=generator,
    )
    val_x = torch.as_tensor(X_val, dtype=torch.float32, device=device)
    val_y = torch.as_tensor(y_val, dtype=torch.long, device=device)
    best_loss, best_state, wait, best_epoch = math.inf, None, 0, 0
    for epoch in range(1, EPOCHS + 1):
        model.train()
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            loss = loss_fn(model(batch_x.to(device)), batch_y.to(device))
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(val_x), val_y).item())
        scheduler.step(val_loss)
        if val_loss < best_loss - 1e-5:
            best_loss = val_loss
            best_state = copy.deepcopy(model.state_dict())
            best_epoch = epoch
            wait = 0
        else:
            wait += 1
            if wait >= PATIENCE:
                break
    if best_state is None:
        raise RuntimeError("LSTM training produced no checkpoint")
    model.load_state_dict(best_state)
    return model, best_epoch


def eer_from_scores(genuine: np.ndarray, impostor: np.ndarray) -> tuple[float, float]:
    labels = np.r_[np.ones(len(genuine), dtype=int), np.zeros(len(impostor), dtype=int)]
    scores = np.r_[genuine, impostor]
    fpr, tpr, thresholds = roc_curve(labels, scores, drop_intermediate=False)
    fnr = 1.0 - tpr
    index = int(np.nanargmin(np.abs(fpr - fnr)))
    return float((fpr[index] + fnr[index]) / 2.0), float(thresholds[index])


def macro_eer(scores: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    eers = []
    for sid in range(scores.shape[1]):
        genuine = scores[y == sid, sid]
        impostor = scores[y != sid, sid]
        if len(genuine) and len(impostor):
            eers.append(eer_from_scores(genuine, impostor)[0])
    return float(np.mean(eers)), float(np.std(eers))


@dataclass
class AdaptiveEMA:
    mean: float
    second_moment: float
    k: float
    alpha: float = AGENT_ALPHA

    @classmethod
    def from_enrollment(cls, scores: np.ndarray, initial_threshold: float) -> "AdaptiveEMA":
        mean = float(np.mean(scores))
        second_moment = float(np.mean(np.square(scores)))
        sigma = math.sqrt(max(second_moment - mean * mean, AGENT_MIN_SIGMA**2))
        k = (mean - initial_threshold) / sigma
        return cls(mean, second_moment, k)

    @property
    def threshold(self) -> float:
        sigma = math.sqrt(max(self.second_moment - self.mean * self.mean, AGENT_MIN_SIGMA**2))
        return max(0.0, self.mean - self.k * sigma)

    def decide(self, score: float) -> bool:
        accepted = score >= self.threshold
        if accepted:
            self.mean = (1.0 - self.alpha) * self.mean + self.alpha * score
            self.second_moment = (
                (1.0 - self.alpha) * self.second_moment + self.alpha * score * score
            )
        return accepted


def chronology_order(session: np.ndarray, within: np.ndarray, indices: np.ndarray) -> np.ndarray:
    return indices[np.lexsort((within[indices], session[indices]))]


def inject_drift(X: np.ndarray, y: np.ndarray, session: np.ndarray, within: np.ndarray,
                 magnitude: float, seed: int) -> np.ndarray:
    if magnitude == 0:
        return X.copy()
    rng = np.random.default_rng(seed)
    direction = rng.normal(size=X.shape[-1])
    direction /= np.linalg.norm(direction) + 1e-12
    drifted = X.copy()
    for sid in np.unique(y):
        indices = chronology_order(session, within, np.flatnonzero(y == sid))
        fractions = np.linspace(0.0, 1.0, len(indices), dtype=np.float32)
        for index, fraction in zip(indices, fractions):
            drifted[index] += (direction * magnitude * fraction)[None, :]
    return drifted


def evaluate_operating_points(
    val_scores: np.ndarray,
    test_scores: np.ndarray,
    y_val: np.ndarray,
    y_test: np.ndarray,
    session_test: np.ndarray,
    within_test: np.ndarray,
    fold: int,
    drift: float,
) -> dict[str, float]:
    static_far, static_frr, adaptive_far, adaptive_frr = [], [], [], []
    rng = np.random.default_rng(SEED + fold * 100 + int(drift * 10))

    for sid in range(test_scores.shape[1]):
        enrollment = val_scores[y_val == sid, sid]
        genuine_idx = chronology_order(session_test, within_test, np.flatnonzero(y_test == sid))
        impostor_pool = np.flatnonzero(y_test != sid)
        if len(enrollment) < 2 or len(genuine_idx) < 2 or len(impostor_pool) < len(genuine_idx):
            continue

        validation_impostor = val_scores[y_val != sid, sid]
        _, tau0 = eer_from_scores(enrollment, validation_impostor)
        s_far, s_frr, a_far, a_frr = [], [], [], []
        for _ in range(STREAM_REPEATS):
            sampled_impostors = rng.choice(impostor_pool, size=len(genuine_idx), replace=False)
            agent = AdaptiveEMA.from_enrollment(enrollment, tau0)
            for genuine_i, impostor_i in zip(genuine_idx, sampled_impostors):
                # Balanced, alternating zero-effort attack stream.  Decisions are
                # label-blind; accepted impostors therefore can poison the agent.
                genuine_score = float(test_scores[genuine_i, sid])
                impostor_score = float(test_scores[impostor_i, sid])
                s_frr.append(genuine_score < tau0)
                s_far.append(impostor_score >= tau0)
                a_frr.append(not agent.decide(genuine_score))
                a_far.append(agent.decide(impostor_score))
        static_far.append(np.mean(s_far))
        static_frr.append(np.mean(s_frr))
        adaptive_far.append(np.mean(a_far))
        adaptive_frr.append(np.mean(a_frr))

    def mean(values: list[float]) -> float:
        return 100.0 * float(np.mean(values))

    return {
        "static_FAR": mean(static_far),
        "static_FRR": mean(static_frr),
        "static_HTER": 0.5 * (mean(static_far) + mean(static_frr)),
        "adaptive_FAR": mean(adaptive_far),
        "adaptive_FRR": mean(adaptive_frr),
        "adaptive_HTER": 0.5 * (mean(adaptive_far) + mean(adaptive_frr)),
    }


def scale_sequences(scaler: StandardScaler, X: np.ndarray) -> np.ndarray:
    n, length, features = X.shape
    return scaler.transform(X.reshape(-1, features)).reshape(n, length, features).astype(np.float32)


def run(args: argparse.Namespace) -> None:
    seed_everything()
    device = choose_device()
    data_dir = Path(args.data_dir).expanduser()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = output_dir / f"hmog_sequences_{args.max_subjects}.npz"
    data = load_or_build_dataset(data_dir, args.max_subjects, cache_path, args.rebuild_cache)
    X, y = data["X"], data["y"]
    session, within = data["session"], data["within_session"]
    n_subjects = len(np.unique(y))
    print(f"dataset: X={X.shape}, subjects={n_subjects}, sessions={len(np.unique(session))}")
    print(f"device: {device}")

    rows = []
    fold_diagnostics = []
    for fold in range(N_FOLDS):
        fit_mask, val_mask, test_mask = fold_masks(session, fold)
        for name, mask in (("fit", fit_mask), ("validation", val_mask), ("test", test_mask)):
            if len(np.unique(y[mask])) != n_subjects:
                raise RuntimeError(f"fold {fold + 1}: {name} does not contain every subject")

        scaler = StandardScaler().fit(X[fit_mask].reshape(-1, X.shape[-1]))
        X_fit = scale_sequences(scaler, X[fit_mask])
        X_val = scale_sequences(scaler, X[val_mask])
        X_test_clean = scale_sequences(scaler, X[test_mask])
        y_fit, y_val, y_test = y[fit_mask], y[val_mask], y[test_mask]
        s_test, w_test = session[test_mask], within[test_mask]

        model, best_epoch = train_lstm(X_fit, y_fit, X_val, y_val, n_subjects, device)
        val_lstm = predict_lstm(model, X_val, device)

        flat_fit, flat_test = X_fit.reshape(len(X_fit), -1), X_test_clean.reshape(len(X_test_clean), -1)
        svm = LinearSVC(
            C=0.1, dual=False, tol=1e-3, random_state=SEED, max_iter=1500
        ).fit(flat_fit, y_fit)
        rf = RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            max_features="sqrt",
            n_jobs=-1,
            random_state=SEED,
        ).fit(flat_fit, y_fit)
        svm_eer, svm_subject_std = macro_eer(svm.decision_function(flat_test), y_test)
        rf_eer, rf_subject_std = macro_eer(rf.predict_proba(flat_test), y_test)

        fold_diagnostics.append(
            {
                "fold": fold + 1,
                "fit_n": int(fit_mask.sum()),
                "validation_n": int(val_mask.sum()),
                "test_n": int(test_mask.sum()),
                "fit_sessions": sorted(map(int, np.unique(session[fit_mask]))),
                "validation_sessions": sorted(map(int, np.unique(session[val_mask]))),
                "test_sessions": sorted(map(int, np.unique(session[test_mask]))),
                "best_epoch": best_epoch,
            }
        )

        for drift in DRIFT_LEVELS:
            X_test = inject_drift(
                X_test_clean, y_test, s_test, w_test, drift, seed=SEED + fold
            )
            lstm_scores = predict_lstm(model, X_test, device)
            lstm_eer, lstm_subject_std = macro_eer(lstm_scores, y_test)
            operating = evaluate_operating_points(
                val_lstm, lstm_scores, y_val, y_test, s_test, w_test, fold, drift
            )
            rows.append(
                {
                    "fold": fold + 1,
                    "drift_l2": drift,
                    "SVM_EER": 100.0 * svm_eer if drift == 0 else np.nan,
                    "RF_EER": 100.0 * rf_eer if drift == 0 else np.nan,
                    "LSTM_EER": 100.0 * lstm_eer,
                    "SVM_subject_EER_std": 100.0 * svm_subject_std if drift == 0 else np.nan,
                    "RF_subject_EER_std": 100.0 * rf_subject_std if drift == 0 else np.nan,
                    "LSTM_subject_EER_std": 100.0 * lstm_subject_std,
                    **operating,
                }
            )
            print(
                f"fold={fold + 1} drift={drift:.1f} LSTM EER={100*lstm_eer:.2f}% "
                f"static/adaptive HTER={operating['static_HTER']:.2f}/{operating['adaptive_HTER']:.2f}%"
            )

        del model
        if device.type == "mps":
            torch.mps.empty_cache()
        elif device.type == "cuda":
            torch.cuda.empty_cache()

    results = pd.DataFrame(rows)
    results.to_csv(output_dir / "revised_results_by_fold.csv", index=False)
    summary_columns = [
        "SVM_EER", "RF_EER", "LSTM_EER", "static_FAR", "static_FRR", "static_HTER",
        "adaptive_FAR", "adaptive_FRR", "adaptive_HTER",
    ]
    summary = results.groupby("drift_l2")[summary_columns].agg(["mean", "std"])
    summary.to_csv(output_dir / "revised_results_summary.csv")
    with open(output_dir / "revised_fold_protocol.json", "w", encoding="utf-8") as handle:
        json.dump(fold_diagnostics, handle, indent=2)

    means = results.groupby("drift_l2").mean(numeric_only=True)
    plt.figure(figsize=(7.2, 4.8))
    plt.plot(means.index, means["static_HTER"], "o-", label="LSTM, frozen threshold")
    plt.plot(means.index, means["adaptive_HTER"], "s-", label="LSTM + EMA agent")
    plt.xlabel(r"Synthetic drift magnitude $\|\delta\|_2$")
    plt.ylabel("HTER (%)")
    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "revised_drift_hter.png", dpi=200)
    plt.close()

    metadata = {
        "seed": SEED,
        "sensor_columns_zero_based": [3, 4, 5],
        "window_size": WINDOW_SIZE,
        "windows_per_session": WINDOWS_PER_SESSION,
        "window_offset": WINDOW_OFFSET,
        "sequence_length": SEQ_LEN,
        "sequence_step": SEQ_STEP,
        "fold_rule": "(session_number - 1) modulo 5",
        "agent_alpha": AGENT_ALPHA,
        "agent_k": "per-subject value induced by validation EER threshold",
        "agent_effective_memory": 1 / AGENT_ALPHA,
        "drift_levels_l2": DRIFT_LEVELS,
        "balanced_stream_repeats": STREAM_REPEATS,
        "n_subjects": n_subjects,
        "n_sequences": len(X),
    }
    with open(output_dir / "revised_experiment_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
    print(summary.round(3))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="~/Downloads/public_dataset")
    parser.add_argument("--output-dir", default="revised_results")
    parser.add_argument("--max-subjects", type=int, default=MAX_SUBJECTS)
    parser.add_argument("--rebuild-cache", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    run(parse_args())
