#!/usr/bin/env python3
"""Locked McGill external replication for Paper 3.

The script implements four explicit stages:

``audit``
    Verify the raw two-day dataset structure without computing model scores.
``train``
    Train and validate the fixed LSTM using Day 1 only. Day 2 is not opened.
``score``
    After the validation gate passes, create the immutable enrollment/Day-2
    score cache. No authentication endpoint is reported at this stage.
``test``
    Consume the fixed cache and run poisoning, guarded-defense, and temporal
    selective-update analyses without retraining or tuning.

Rates are fractions internally and percentages in exported CSV files. Profile
statistics remain in native softmax-score units.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import platform
import random
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


PROTOCOL_ID = "paper3-external-mcgill-v1"
SUBJECT_PATTERN = re.compile(r"w(?P<sid>\d{3})day(?P<day>[12])-raw\.csv$")
REQUIRED_COLUMNS = ("timestamp", "accel_x", "accel_y", "accel_z", "accel_mag")
METHODS_ATTACK = ("Frozen", "Blind EMA", "Guarded EMA")
METHODS_TEMPORAL = ("Frozen", "Guarded EMA", "Oracle-all-genuine")
RATE_COLUMNS = {
    "post_ASR", "FAR", "post_FRR", "HTER", "MUR", "GUR",
    "poison_accept_rate", "genuine_auth_rate", "early_FRR", "late_FRR",
    "early_FAR", "late_FAR", "early_HTER", "late_HTER", "value",
    "mean", "ci_low", "ci_high",
}


class ProtocolError(RuntimeError):
    """Raised when a locked protocol invariant is violated."""


class BoundaryInfeasible(RuntimeError):
    """Raised when fewer than max-K initially accepted candidates exist."""


class ValidationGateFailed(RuntimeError):
    """Raised when the frozen Day-1-only model viability gate fails."""


@dataclass(frozen=True)
class DatasetAuditRow:
    sid: int
    day: int
    filename: str
    rows: int
    windows: int
    duration_minutes: float
    median_interval_ms: float
    nonincreasing_timestamps: int
    gaps_over_500ms: int
    missing_required_rows: int
    sha256: str


@dataclass
class EMAProfile:
    mu: float
    q: float
    k: float
    alpha: float = 0.05
    min_sigma: float = 1e-4

    @classmethod
    def from_enrollment(
        cls,
        scores: Sequence[float],
        threshold: float,
        *,
        alpha: float,
        min_sigma: float,
    ) -> "EMAProfile":
        values = np.asarray(scores, dtype=float)
        if values.size == 0 or not np.all(np.isfinite(values)):
            raise ProtocolError("Enrollment scores must be finite and non-empty")
        mu = float(np.mean(values))
        q = float(np.mean(values * values))
        sigma = max(math.sqrt(max(q - mu * mu, 0.0)), min_sigma)
        k = (mu - float(threshold)) / sigma
        return cls(mu=mu, q=q, k=k, alpha=alpha, min_sigma=min_sigma)

    @property
    def sigma(self) -> float:
        return max(math.sqrt(max(self.q - self.mu * self.mu, 0.0)), self.min_sigma)

    @property
    def threshold(self) -> float:
        return self.mu - self.k * self.sigma

    def update(self, score: float) -> None:
        value = float(score)
        self.mu = (1.0 - self.alpha) * self.mu + self.alpha * value
        self.q = (1.0 - self.alpha) * self.q + self.alpha * value * value


class McGillLSTM(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, classes: int):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=False,
        )
        self.output = nn.Linear(hidden_size, classes)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        _, (hidden, _) = self.lstm(inputs)
        return self.output(hidden[-1])


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_protocol(path: Path) -> dict:
    protocol = json.loads(path.read_text(encoding="utf-8"))
    if protocol.get("protocol_id") != PROTOCOL_ID:
        raise ProtocolError(
            f"Expected protocol_id={PROTOCOL_ID!r}, got {protocol.get('protocol_id')!r}"
        )
    fixed = {
        "window_samples": 128,
        "overlap_samples": 0,
        "subjects": 20,
    }
    for key, expected in fixed.items():
        actual = protocol["dataset"].get(key)
        if actual != expected:
            raise ProtocolError(f"Locked dataset.{key} must be {expected}, got {actual}")
    if protocol["profile"].get("guarded_lambda") != 0.25:
        raise ProtocolError("Locked guarded lambda must remain 0.25")
    if protocol["attack"].get("budgets") != [0, 1, 2, 4, 8]:
        raise ProtocolError("Locked attack budgets must remain [0,1,2,4,8]")
    return protocol


def git_revision(project_dir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project_dir, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def environment_snapshot() -> dict[str, object]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "torch": torch.__version__,
        "torch_threads": torch.get_num_threads(),
    }


def discover_files(data_dir: Path) -> dict[tuple[int, int], Path]:
    found: dict[tuple[int, int], Path] = {}
    for path in sorted(data_dir.glob("w*day*-raw.csv")):
        match = SUBJECT_PATTERN.fullmatch(path.name)
        if not match:
            continue
        key = (int(match.group("sid")), int(match.group("day")))
        if key in found:
            raise ProtocolError(f"Duplicate file for subject/day {key}")
        found[key] = path
    expected = {(sid, day) for sid in range(1, 21) for day in (1, 2)}
    missing = sorted(expected.difference(found))
    extra = sorted(set(found).difference(expected))
    if missing or extra:
        raise ProtocolError(f"Dataset files mismatch; missing={missing}, extra={extra}")
    return found


def read_raw(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t")
    absent = [name for name in REQUIRED_COLUMNS if name not in frame.columns]
    if absent:
        raise ProtocolError(f"{path.name} is missing columns {absent}")
    return frame.loc[:, REQUIRED_COLUMNS].copy()


def frame_to_windows(frame: pd.DataFrame, window_samples: int) -> np.ndarray:
    values = frame.loc[:, REQUIRED_COLUMNS[1:]].to_numpy(dtype=np.float32)
    if not np.all(np.isfinite(values)):
        raise ProtocolError("Required sensor channels contain non-finite values")
    count = len(values) // window_samples
    if count == 0:
        return np.empty((0, window_samples, len(REQUIRED_COLUMNS) - 1), dtype=np.float32)
    return values[: count * window_samples].reshape(count, window_samples, -1)


def audit_dataset(data_dir: Path, protocol: dict) -> tuple[pd.DataFrame, list[int]]:
    files = discover_files(data_dir)
    window_samples = int(protocol["dataset"]["window_samples"])
    rows: list[DatasetAuditRow] = []
    eligible: list[int] = []
    by_subject: dict[int, dict[int, DatasetAuditRow]] = {}
    for (sid, day), path in sorted(files.items()):
        frame = read_raw(path)
        timestamps = frame["timestamp"].to_numpy(dtype=np.int64)
        delta = np.diff(timestamps)
        positive = delta[delta > 0]
        row = DatasetAuditRow(
            sid=sid,
            day=day,
            filename=path.name,
            rows=len(frame),
            windows=len(frame) // window_samples,
            duration_minutes=float((timestamps[-1] - timestamps[0]) / 60000.0),
            median_interval_ms=float(np.median(positive)) if positive.size else float("nan"),
            nonincreasing_timestamps=int(np.sum(delta <= 0)),
            gaps_over_500ms=int(np.sum(delta > 500)),
            missing_required_rows=int(frame.isna().any(axis=1).sum()),
            sha256=sha256_file(path),
        )
        rows.append(row)
        by_subject.setdefault(sid, {})[day] = row

    for sid in range(1, 21):
        day1 = by_subject[sid][1]
        day2 = by_subject[sid][2]
        valid = (
            day1.windows >= 100
            and day2.windows >= 160
            and day1.nonincreasing_timestamps == 0
            and day2.nonincreasing_timestamps == 0
            and day1.missing_required_rows == 0
            and day2.missing_required_rows == 0
        )
        if valid:
            eligible.append(sid)
    return pd.DataFrame(asdict(row) for row in rows), eligible


def chronological_day1_split(windows: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    count = len(windows)
    first = math.floor(0.60 * count)
    second = math.floor(0.80 * count)
    if first <= 0 or second <= first or second >= count:
        raise ProtocolError(f"Cannot split {count} Day-1 windows into 60/20/20")
    return windows[:first], windows[first:second], windows[second:]


def temporal_selection_indices(total_windows: int, selected_windows: int = 160) -> np.ndarray:
    if total_windows < selected_windows:
        raise ProtocolError(
            f"Need {selected_windows} Day-2 windows, found {total_windows}"
        )
    indices = np.rint(np.linspace(0, total_windows - 1, selected_windows)).astype(np.int64)
    if len(np.unique(indices)) != selected_windows:
        raise ProtocolError("Temporal selection produced duplicate indices")
    return indices


def fit_normalization(training: Sequence[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    flat = np.concatenate([item.reshape(-1, item.shape[-1]) for item in training], axis=0)
    mean = np.mean(flat, axis=0, dtype=np.float64)
    std = np.std(flat, axis=0, dtype=np.float64)
    std = np.where(std < 1e-8, 1.0, std)
    return mean.astype(np.float32), std.astype(np.float32)


def normalize_windows(windows: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    return ((windows - mean[None, None, :]) / std[None, None, :]).astype(np.float32)


def stack_labeled(parts: dict[int, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    subject_ids = np.asarray(sorted(parts), dtype=np.int16)
    arrays = [parts[int(sid)] for sid in subject_ids]
    features = np.concatenate(arrays, axis=0).astype(np.float32)
    labels = np.concatenate(
        [np.full(len(array), index, dtype=np.int64) for index, array in enumerate(arrays)]
    )
    source_subjects = np.concatenate(
        [np.full(len(array), sid, dtype=np.int16) for sid, array in zip(subject_ids, arrays)]
    )
    return features, labels, source_subjects


def set_determinism(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))


def evaluate_model(
    model: nn.Module,
    features: np.ndarray,
    labels: np.ndarray,
    criterion: nn.Module,
    batch_size: int,
) -> tuple[float, float]:
    loader = DataLoader(
        TensorDataset(torch.from_numpy(features), torch.from_numpy(labels)),
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )
    model.eval()
    total_loss = total_correct = total_count = 0
    with torch.no_grad():
        for inputs, targets in loader:
            logits = model(inputs)
            total_loss += float(criterion(logits, targets).item()) * len(targets)
            total_correct += int((logits.argmax(dim=1) == targets).sum().item())
            total_count += len(targets)
    return total_loss / total_count, total_correct / total_count


def predict_probabilities(model: nn.Module, features: np.ndarray, batch_size: int) -> np.ndarray:
    loader = DataLoader(
        TensorDataset(torch.from_numpy(features)),
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )
    model.eval()
    batches: list[np.ndarray] = []
    with torch.no_grad():
        for (inputs,) in loader:
            batches.append(torch.softmax(model(inputs), dim=1).cpu().numpy())
    return np.concatenate(batches, axis=0).astype(np.float32)


def run_training(
    data_dir: Path,
    cache_dir: Path,
    protocol_path: Path,
    project_dir: Path,
) -> dict:
    protocol = load_protocol(protocol_path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = cache_dir / "model_day1.pt"
    manifest_path = cache_dir / "training_manifest.json"
    if checkpoint_path.exists() or manifest_path.exists():
        raise FileExistsError("Training artifacts already exist; refusing to overwrite")

    files = discover_files(data_dir)
    window_samples = int(protocol["dataset"]["window_samples"])
    train_parts: dict[int, np.ndarray] = {}
    val_parts: dict[int, np.ndarray] = {}
    day1_counts: dict[str, dict[str, int]] = {}
    for sid in range(1, 21):
        windows = frame_to_windows(read_raw(files[(sid, 1)]), window_samples)
        train, validation, enrollment = chronological_day1_split(windows)
        train_parts[sid] = train
        val_parts[sid] = validation
        day1_counts[str(sid)] = {
            "train": len(train), "validation": len(validation), "enrollment": len(enrollment)
        }

    norm_mean, norm_std = fit_normalization(list(train_parts.values()))
    train_parts = {
        sid: normalize_windows(values, norm_mean, norm_std)
        for sid, values in train_parts.items()
    }
    val_parts = {
        sid: normalize_windows(values, norm_mean, norm_std)
        for sid, values in val_parts.items()
    }
    x_train, y_train, _ = stack_labeled(train_parts)
    x_val, y_val, _ = stack_labeled(val_parts)

    represented_classes = int(len(np.unique(y_val)))
    minimum_classes = int(protocol["test_gate"]["minimum_validation_classes"])
    if represented_classes < minimum_classes:
        raise ValidationGateFailed(
            f"Validation has {represented_classes} classes, below {minimum_classes}"
        )

    model_cfg = protocol["model"]
    seed = int(protocol["seeds"]["model"])
    set_determinism(seed)
    model = McGillLSTM(
        input_size=int(model_cfg["input_size"]),
        hidden_size=int(model_cfg["hidden_size"]),
        classes=int(model_cfg["classes"]),
    )
    counts = np.bincount(y_train, minlength=int(model_cfg["classes"]))
    class_weights = len(y_train) / (len(counts) * counts.astype(float))
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(class_weights, dtype=torch.float32))
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=float(model_cfg["learning_rate"]),
        weight_decay=float(model_cfg["weight_decay"]),
    )
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(
        TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train)),
        batch_size=int(model_cfg["batch_size"]),
        shuffle=True,
        generator=generator,
        num_workers=0,
    )

    best_state: dict[str, torch.Tensor] | None = None
    best_loss = float("inf")
    best_accuracy = 0.0
    bad_epochs = 0
    history: list[dict[str, float | int]] = []
    started = time.perf_counter()
    for epoch in range(1, int(model_cfg["max_epochs"]) + 1):
        model.train()
        train_loss_sum = 0.0
        train_count = 0
        for inputs, targets in loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(inputs)
            loss = criterion(logits, targets)
            if not torch.isfinite(loss):
                raise ValidationGateFailed("Non-finite training loss")
            loss.backward()
            optimizer.step()
            train_loss_sum += float(loss.item()) * len(targets)
            train_count += len(targets)
        val_loss, val_accuracy = evaluate_model(
            model, x_val, y_val, criterion, int(model_cfg["batch_size"])
        )
        history.append({
            "epoch": epoch,
            "train_loss": train_loss_sum / train_count,
            "validation_loss": val_loss,
            "validation_top1": val_accuracy,
        })
        if val_loss < best_loss - 1e-8:
            best_loss = val_loss
            best_accuracy = val_accuracy
            best_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
            bad_epochs = 0
        else:
            bad_epochs += 1
            if bad_epochs >= int(model_cfg["patience"]):
                break

    if best_state is None:
        raise ValidationGateFailed("No finite validation checkpoint was produced")
    minimum_accuracy = float(protocol["test_gate"]["minimum_validation_top1"])
    gate_passed = best_accuracy >= minimum_accuracy
    pd.DataFrame(history).to_csv(cache_dir / "training_history.csv", index=False)
    manifest = {
        "protocol_id": PROTOCOL_ID,
        "protocol_sha256": sha256_file(protocol_path),
        "created_at": utc_now(),
        "git_revision": git_revision(project_dir),
        "day2_loaded": False,
        "status": "validation_passed" if gate_passed else "validation_failed",
        "best_validation_loss": best_loss,
        "best_validation_top1": best_accuracy,
        "minimum_validation_top1": minimum_accuracy,
        "epochs_completed": len(history),
        "training_seconds": time.perf_counter() - started,
        "day1_counts": day1_counts,
        "normalization_mean": norm_mean.tolist(),
        "normalization_std": norm_std.tolist(),
        "environment": environment_snapshot(),
    }
    write_json(manifest_path, manifest)
    if not gate_passed:
        raise ValidationGateFailed(
            f"Validation top-1 {best_accuracy:.4f} is below locked gate {minimum_accuracy:.4f}"
        )
    torch.save(
        {
            "state_dict": best_state,
            "normalization_mean": norm_mean,
            "normalization_std": norm_std,
            "protocol_sha256": sha256_file(protocol_path),
            "model_config": model_cfg,
        },
        checkpoint_path,
    )
    return manifest


def load_trained_model(cache_dir: Path, protocol_path: Path) -> tuple[McGillLSTM, np.ndarray, np.ndarray]:
    manifest = json.loads((cache_dir / "training_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "validation_passed" or manifest.get("day2_loaded") is not False:
        raise ProtocolError("Training manifest does not document a passed Day-1-only gate")
    expected_hash = sha256_file(protocol_path)
    if manifest.get("protocol_sha256") != expected_hash:
        raise ProtocolError("Protocol changed after Day-1 training")
    # This checkpoint is created locally by ``run_training`` after the locked
    # Day-1 validation gate. It also contains NumPy normalization arrays, which
    # PyTorch's restricted weights-only loader intentionally rejects.
    payload = torch.load(cache_dir / "model_day1.pt", map_location="cpu", weights_only=False)
    if payload.get("protocol_sha256") != expected_hash:
        raise ProtocolError("Checkpoint protocol hash mismatch")
    cfg = payload["model_config"]
    model = McGillLSTM(int(cfg["input_size"]), int(cfg["hidden_size"]), int(cfg["classes"]))
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return (
        model,
        np.asarray(payload["normalization_mean"], dtype=np.float32),
        np.asarray(payload["normalization_std"], dtype=np.float32),
    )


def create_score_cache(
    data_dir: Path,
    cache_dir: Path,
    protocol_path: Path,
    project_dir: Path,
) -> dict:
    protocol = load_protocol(protocol_path)
    score_path = cache_dir / "scores_mcgill_day2.npz"
    manifest_path = cache_dir / "score_manifest.json"
    if score_path.exists() or manifest_path.exists():
        raise FileExistsError("Score cache already exists; refusing to overwrite")
    model, norm_mean, norm_std = load_trained_model(cache_dir, protocol_path)
    files = discover_files(data_dir)
    window_samples = int(protocol["dataset"]["window_samples"])
    batch_size = int(protocol["model"]["batch_size"])
    enroll_parts: dict[int, np.ndarray] = {}
    day2_parts: dict[int, np.ndarray] = {}
    for sid in range(1, 21):
        day1_windows = frame_to_windows(read_raw(files[(sid, 1)]), window_samples)
        _, _, enrollment = chronological_day1_split(day1_windows)
        enroll_parts[sid] = normalize_windows(enrollment, norm_mean, norm_std)
        day2_windows = frame_to_windows(read_raw(files[(sid, 2)]), window_samples)
        day2_parts[sid] = normalize_windows(day2_windows, norm_mean, norm_std)

    x_enroll, _, enroll_subjects = stack_labeled(enroll_parts)
    x_day2, _, day2_subjects = stack_labeled(day2_parts)
    enroll_scores = predict_probabilities(model, x_enroll, batch_size)
    day2_scores = predict_probabilities(model, x_day2, batch_size)
    enroll_within = np.concatenate(
        [np.arange(len(enroll_parts[sid]), dtype=np.int32) for sid in sorted(enroll_parts)]
    )
    day2_within = np.concatenate(
        [np.arange(len(day2_parts[sid]), dtype=np.int32) for sid in sorted(day2_parts)]
    )
    np.savez_compressed(
        score_path,
        subject_ids=np.arange(1, 21, dtype=np.int16),
        enroll_scores=enroll_scores,
        enroll_subjects=enroll_subjects,
        enroll_within=enroll_within,
        day2_scores=day2_scores,
        day2_subjects=day2_subjects,
        day2_within=day2_within,
    )
    raw_hashes = {path.name: sha256_file(path) for path in files.values()}
    manifest = {
        "protocol_id": PROTOCOL_ID,
        "protocol_sha256": sha256_file(protocol_path),
        "created_at": utc_now(),
        "git_revision": git_revision(project_dir),
        "status": "score_cache_complete",
        "day2_loaded": True,
        "endpoints_computed": False,
        "score_cache": score_path.name,
        "score_cache_sha256": sha256_file(score_path),
        "raw_file_sha256": raw_hashes,
        "n_enrollment_windows": len(enroll_scores),
        "n_day2_windows": len(day2_scores),
        "environment": environment_snapshot(),
    }
    write_json(manifest_path, manifest)
    return manifest


def load_score_cache(cache_dir: Path, protocol_path: Path) -> dict[str, np.ndarray]:
    manifest = json.loads((cache_dir / "score_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "score_cache_complete":
        raise ProtocolError("Score cache is not complete")
    if manifest.get("protocol_sha256") != sha256_file(protocol_path):
        raise ProtocolError("Protocol changed after score-cache generation")
    path = cache_dir / manifest["score_cache"]
    if sha256_file(path) != manifest.get("score_cache_sha256"):
        raise ProtocolError("Score cache hash mismatch")
    with np.load(path) as data:
        return {name: np.asarray(data[name]) for name in data.files}


def calibrate_threshold(genuine: Sequence[float], impostor: Sequence[float]) -> float:
    genuine_array = np.asarray(genuine, dtype=float)
    impostor_array = np.asarray(impostor, dtype=float)
    if genuine_array.size == 0 or impostor_array.size == 0:
        raise ProtocolError("Threshold calibration needs genuine and impostor scores")
    values = np.unique(np.concatenate([genuine_array, impostor_array]))
    lower = np.nextafter(values[0], -np.inf)
    upper = np.nextafter(values[-1], np.inf)
    midpoints = (values[:-1] + values[1:]) / 2.0
    candidates = np.concatenate([[lower], midpoints, [upper]])
    best_hter = float("inf")
    best_threshold = float(candidates[0])
    for threshold in candidates:
        frr = float(np.mean(genuine_array < threshold))
        far = float(np.mean(impostor_array >= threshold))
        hter = 0.5 * (frr + far)
        if hter < best_hter - 1e-15 or (
            abs(hter - best_hter) <= 1e-15 and threshold > best_threshold
        ):
            best_hter = hter
            best_threshold = float(threshold)
    return best_threshold


def initial_profiles(cache: dict[str, np.ndarray], protocol: dict) -> dict[int, tuple[np.ndarray, float]]:
    scores = cache["enroll_scores"]
    subjects = cache["enroll_subjects"]
    output: dict[int, tuple[np.ndarray, float]] = {}
    for victim in range(1, 21):
        genuine = scores[subjects == victim, victim - 1].astype(float)
        impostor = scores[subjects != victim, victim - 1].astype(float)
        output[victim] = (genuine, calibrate_threshold(genuine, impostor))
    return output


def split_source_identities(
    source_ids: Sequence[int], rng: np.random.Generator, probe_fraction: float
) -> tuple[np.ndarray, np.ndarray]:
    identities = np.asarray(sorted(set(int(value) for value in source_ids)), dtype=np.int16)
    if len(identities) < 2:
        raise ProtocolError("Need at least two source identities")
    shuffled = identities[rng.permutation(len(identities))]
    probe_count = int(round(len(identities) * probe_fraction))
    probe_count = min(max(probe_count, 1), len(identities) - 1)
    probe = np.sort(shuffled[:probe_count])
    poison = np.sort(shuffled[probe_count:])
    return poison, probe


def source_temporal_pool(
    subjects: np.ndarray,
    within: np.ndarray,
    selected_sources: Sequence[int],
    *,
    half: str,
) -> np.ndarray:
    pieces: list[np.ndarray] = []
    for sid in selected_sources:
        indices = np.flatnonzero(subjects == sid)
        indices = indices[np.argsort(within[indices], kind="stable")]
        cut = len(indices) // 2
        chosen = indices[:cut] if half == "first" else indices[cut:]
        pieces.append(chosen)
    return np.concatenate(pieces).astype(np.int64)


def choose_poison_sequence(
    strategy: str,
    pool: np.ndarray,
    victim_scores: np.ndarray,
    threshold: float,
    max_budget: int,
    rng: np.random.Generator,
) -> np.ndarray:
    pool = np.asarray(pool, dtype=np.int64)
    if len(pool) < max_budget:
        raise ProtocolError(f"Poison pool has {len(pool)} samples, needs {max_budget}")
    if strategy == "random":
        return rng.choice(pool, size=max_budget, replace=False).astype(np.int64)
    if strategy == "boundary":
        candidate_scores = victim_scores[pool]
        accepted = candidate_scores >= threshold
        accepted_indices = pool[accepted]
        accepted_scores = candidate_scores[accepted]
        if len(accepted_indices) < max_budget:
            raise BoundaryInfeasible(
                f"Only {len(accepted_indices)} accepted candidates for K={max_budget}"
            )
        order = np.lexsort((accepted_indices, accepted_scores - threshold))
        return accepted_indices[order[:max_budget]].astype(np.int64)
    raise ValueError(f"Unknown strategy {strategy!r}")


def profile_snapshot(profile: EMAProfile) -> dict[str, float]:
    return {"mean": profile.mu, "sigma": profile.sigma, "threshold": profile.threshold}


def apply_stream(
    profile: EMAProfile,
    scores: Iterable[float],
    method: str,
    mu_enroll: float,
    guarded_lambda: float,
    *,
    genuine: bool,
) -> tuple[int, int]:
    accepted = updates = 0
    for raw_score in scores:
        score = float(raw_score)
        authenticated = score >= profile.threshold
        accepted += int(authenticated)
        update = False
        if method == "Blind EMA":
            update = authenticated
        elif method == "Guarded EMA":
            update_threshold = profile.threshold + guarded_lambda * (mu_enroll - profile.threshold)
            update = authenticated and score >= update_threshold
        elif method == "Oracle-all-genuine":
            update = genuine
        elif method != "Frozen":
            raise ValueError(f"Unknown method {method!r}")
        if update:
            profile.update(score)
            updates += 1
    return accepted, updates


def evaluate_attack_method(
    method: str,
    enrollment: np.ndarray,
    threshold: float,
    poison_scores: np.ndarray,
    probe_scores: np.ndarray,
    genuine_scores: np.ndarray,
    protocol: dict,
) -> dict[str, float | int | str]:
    profile_cfg = protocol["profile"]
    profile = EMAProfile.from_enrollment(
        enrollment,
        threshold,
        alpha=float(profile_cfg["alpha"]),
        min_sigma=float(profile_cfg["min_sigma"]),
    )
    before = profile_snapshot(profile)
    accepted, updates = apply_stream(
        profile,
        poison_scores,
        method,
        float(np.mean(enrollment)),
        float(profile_cfg["guarded_lambda"]),
        genuine=False,
    )
    after = profile_snapshot(profile)
    post_asr = float(np.mean(probe_scores >= after["threshold"]))
    post_frr = float(np.mean(genuine_scores < after["threshold"]))
    denominator = len(poison_scores)
    return {
        "method": method,
        "post_ASR": post_asr,
        "FAR": post_asr,
        "post_FRR": post_frr,
        "HTER": 0.5 * (post_asr + post_frr),
        "poison_accepts": accepted,
        "poison_accept_rate": accepted / denominator if denominator else 0.0,
        "malicious_updates": updates,
        "MUR": updates / denominator if denominator else 0.0,
        "mean_before": before["mean"],
        "mean_after": after["mean"],
        "mean_delta": after["mean"] - before["mean"],
        "sigma_before": before["sigma"],
        "sigma_after": after["sigma"],
        "sigma_delta": after["sigma"] - before["sigma"],
        "threshold_before": before["threshold"],
        "threshold_after": after["threshold"],
        "threshold_delta": after["threshold"] - before["threshold"],
    }


def run_attack_block(
    cache: dict[str, np.ndarray], protocol: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    profiles = initial_profiles(cache, protocol)
    scores = cache["day2_scores"]
    subjects = cache["day2_subjects"]
    within = cache["day2_within"]
    budgets = [int(value) for value in protocol["attack"]["budgets"]]
    max_budget = max(budgets)
    repeats = int(protocol["attack"]["repeats"])
    probe_fraction = float(protocol["attack"]["probe_fraction"])
    master_seed = int(protocol["seeds"]["attack"])
    rows: list[dict[str, object]] = []
    exclusions: list[dict[str, object]] = []

    for victim in range(1, 21):
        enrollment, threshold = profiles[victim]
        victim_scores = scores[:, victim - 1].astype(float)
        genuine_scores = victim_scores[subjects == victim]
        source_ids = [sid for sid in range(1, 21) if sid != victim]
        for repeat in range(repeats):
            split_rng = np.random.default_rng(
                np.random.SeedSequence([master_seed, victim, repeat, 0])
            )
            poison_sources, probe_sources = split_source_identities(
                source_ids, split_rng, probe_fraction
            )
            poison_pool = source_temporal_pool(
                subjects, within, poison_sources, half="first"
            )
            probe_pool = source_temporal_pool(
                subjects, within, probe_sources, half="second"
            )
            probe_scores = victim_scores[probe_pool]
            for strategy_code, strategy in enumerate(protocol["attack"]["strategies"]):
                sequence_rng = np.random.default_rng(
                    np.random.SeedSequence([master_seed, victim, repeat, strategy_code + 1])
                )
                try:
                    sequence = choose_poison_sequence(
                        strategy,
                        poison_pool,
                        victim_scores,
                        threshold,
                        max_budget,
                        sequence_rng,
                    )
                except BoundaryInfeasible as exc:
                    exclusions.append({
                        "block": "attack",
                        "strategy": strategy,
                        "victim": victim,
                        "repeat": repeat,
                        "reason": str(exc),
                    })
                    continue
                for budget in budgets:
                    prefix = sequence[:budget]
                    poison_scores = victim_scores[prefix]
                    for method in METHODS_ATTACK:
                        result = evaluate_attack_method(
                            method,
                            enrollment,
                            threshold,
                            poison_scores,
                            probe_scores,
                            genuine_scores,
                            protocol,
                        )
                        rows.append({
                            "victim": victim,
                            "repeat": repeat,
                            "strategy": strategy,
                            "K": budget,
                            "n_poison_sources": len(poison_sources),
                            "n_probe_sources": len(probe_sources),
                            "n_poison_candidates": len(poison_pool),
                            "n_probe_samples": len(probe_pool),
                            "n_genuine_samples": len(genuine_scores),
                            **result,
                        })
    return pd.DataFrame(rows), pd.DataFrame(exclusions)


def run_temporal_block(cache: dict[str, np.ndarray], protocol: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    profiles = initial_profiles(cache, protocol)
    scores = cache["day2_scores"]
    subjects = cache["day2_subjects"]
    within = cache["day2_within"]
    selected_count = int(protocol["temporal"]["selected_day2_windows"])
    early_count = int(protocol["temporal"]["early_units"])
    late_count = int(protocol["temporal"]["late_units"])
    profile_cfg = protocol["profile"]
    subject_indices: dict[int, np.ndarray] = {}
    for sid in range(1, 21):
        indices = np.flatnonzero(subjects == sid)
        indices = indices[np.argsort(within[indices], kind="stable")]
        selected = temporal_selection_indices(len(indices), selected_count)
        subject_indices[sid] = indices[selected]

    checkpoint_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for victim in range(1, 21):
        enrollment, threshold = profiles[victim]
        mu_enroll = float(np.mean(enrollment))
        victim_selected = subject_indices[victim]
        for method in METHODS_TEMPORAL:
            profile = EMAProfile.from_enrollment(
                enrollment,
                threshold,
                alpha=float(profile_cfg["alpha"]),
                min_sigma=float(profile_cfg["min_sigma"]),
            )
            before = profile_snapshot(profile)
            updates = accepted = 0
            method_rows: list[dict[str, object]] = []
            for unit in range(selected_count // 2):
                adaptation_index = victim_selected[2 * unit]
                checkpoint_index = victim_selected[2 * unit + 1]
                adaptation_score = float(scores[adaptation_index, victim - 1])
                accepted_now, updated_now = apply_stream(
                    profile,
                    [adaptation_score],
                    method,
                    mu_enroll,
                    float(profile_cfg["guarded_lambda"]),
                    genuine=True,
                )
                accepted += accepted_now
                updates += updated_now
                checkpoint_score = float(scores[checkpoint_index, victim - 1])
                checkpoint_rejected = float(checkpoint_score < profile.threshold)
                impostor_scores = []
                for source in range(1, 21):
                    if source == victim:
                        continue
                    source_checkpoint = subject_indices[source][2 * unit + 1]
                    impostor_scores.append(float(scores[source_checkpoint, victim - 1]))
                far = float(np.mean(np.asarray(impostor_scores) >= profile.threshold))
                row = {
                    "victim": victim,
                    "method": method,
                    "unit": unit,
                    "adaptation_score": adaptation_score,
                    "adaptation_authenticated": accepted_now,
                    "update_event": updated_now,
                    "checkpoint_score": checkpoint_score,
                    "checkpoint_FRR": checkpoint_rejected,
                    "checkpoint_FAR": far,
                    "mean": profile.mu,
                    "sigma": profile.sigma,
                    "threshold": profile.threshold,
                }
                checkpoint_rows.append(row)
                method_rows.append(row)
            after = profile_snapshot(profile)
            method_frame = pd.DataFrame(method_rows)
            early = method_frame.iloc[:early_count]
            late = method_frame.iloc[-late_count:]
            early_frr = float(early["checkpoint_FRR"].mean())
            late_frr = float(late["checkpoint_FRR"].mean())
            early_far = float(early["checkpoint_FAR"].mean())
            late_far = float(late["checkpoint_FAR"].mean())
            summary_rows.append({
                "victim": victim,
                "method": method,
                "n_units": len(method_frame),
                "genuine_authentications": accepted,
                "genuine_updates": updates,
                "genuine_auth_rate": accepted / len(method_frame),
                "GUR": updates / len(method_frame),
                "early_FRR": early_frr,
                "late_FRR": late_frr,
                "early_FAR": early_far,
                "late_FAR": late_far,
                "early_HTER": 0.5 * (early_frr + early_far),
                "late_HTER": 0.5 * (late_frr + late_far),
                "mean_before": before["mean"],
                "mean_after": after["mean"],
                "mean_delta": after["mean"] - before["mean"],
                "sigma_before": before["sigma"],
                "sigma_after": after["sigma"],
                "sigma_delta": after["sigma"] - before["sigma"],
                "threshold_before": before["threshold"],
                "threshold_after": after["threshold"],
                "threshold_delta": after["threshold"] - before["threshold"],
            })
    return pd.DataFrame(checkpoint_rows), pd.DataFrame(summary_rows)


def bootstrap_mean(values: np.ndarray, samples: int, rng: np.random.Generator) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    if array.size == 0 or not np.all(np.isfinite(array)):
        raise ProtocolError("Bootstrap values must be finite and non-empty")
    indices = rng.integers(0, len(array), size=(samples, len(array)))
    estimates = array[indices].mean(axis=1)
    return float(array.mean()), float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))


def summarize_absolute(
    frame: pd.DataFrame,
    group_columns: Sequence[str],
    metrics: Sequence[str],
    protocol: dict,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    samples = int(protocol["bootstrap_samples"])
    master_seed = int(protocol["seeds"]["bootstrap"])
    for group_number, (keys, group) in enumerate(frame.groupby(list(group_columns), sort=True)):
        if not isinstance(keys, tuple):
            keys = (keys,)
        labels = dict(zip(group_columns, keys))
        for metric_number, metric in enumerate(metrics):
            rng = np.random.default_rng(
                np.random.SeedSequence([master_seed, group_number, metric_number, 1])
            )
            mean, low, high = bootstrap_mean(group[metric].to_numpy(), samples, rng)
            rows.append({
                **labels,
                "metric": metric,
                "n_subjects": int(group["victim"].nunique()),
                "mean": mean,
                "ci_low": low,
                "ci_high": high,
            })
    return pd.DataFrame(rows)


def paired_effect(
    frame: pd.DataFrame,
    index_columns: Sequence[str],
    condition: dict[str, object],
    metric: str,
    method_a: str,
    method_b: str,
    protocol: dict,
    label: str,
    seed_offset: int,
) -> dict[str, object]:
    selected = frame.copy()
    for column, value in condition.items():
        selected = selected[selected[column] == value]
    pivot = selected.pivot_table(index=list(index_columns), columns="method", values=metric, aggfunc="mean")
    paired = pivot[[method_a, method_b]].dropna()
    values = paired[method_a].to_numpy() - paired[method_b].to_numpy()
    rng = np.random.default_rng(
        np.random.SeedSequence([int(protocol["seeds"]["bootstrap"]), seed_offset])
    )
    mean, low, high = bootstrap_mean(values, int(protocol["bootstrap_samples"]), rng)
    return {
        "contrast": label,
        **condition,
        "metric": metric,
        "method_a": method_a,
        "method_b": method_b,
        "effect_definition": "method_a_minus_method_b",
        "n_subjects": len(paired),
        "mean_effect": mean,
        "ci_low": low,
        "ci_high": high,
    }


def percentage_export(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    output = frame.copy()
    for column in columns:
        if column in output.columns:
            output[column] = 100.0 * output[column]
    return output


def create_figures(
    attack_subject: pd.DataFrame,
    temporal_subject: pd.DataFrame,
    checkpoints: pd.DataFrame,
    output_dir: Path,
) -> list[Path]:
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    colors = {"Frozen": "#4C566A", "Blind EMA": "#BF616A", "Guarded EMA": "#2A9D8F", "Oracle-all-genuine": "#5E3C99"}

    plot_data = (
        attack_subject.groupby(["strategy", "K", "method"], as_index=False)["post_ASR"].mean()
    )
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for axis, strategy in zip(axes, ("random", "boundary")):
        subset = plot_data[plot_data["strategy"] == strategy]
        for method in METHODS_ATTACK:
            line = subset[subset["method"] == method]
            axis.plot(line["K"], 100.0 * line["post_ASR"], marker="o", label=method, color=colors[method])
        axis.set_title(strategy.capitalize())
        axis.set_xlabel("Poisoning budget K")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Held-out post-poison ASR (%)")
    axes[1].legend(frameon=False)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        path = figure_dir / f"external_poisoning_asr.{suffix}"
        fig.savefig(path, dpi=220, bbox_inches="tight")
        created.append(path)
    plt.close(fig)

    tradeoff = temporal_subject.groupby("method", as_index=False)[["late_FAR", "late_FRR"]].mean()
    fig, axis = plt.subplots(figsize=(6, 5))
    for _, row in tradeoff.iterrows():
        method = str(row["method"])
        axis.scatter(100.0 * row["late_FAR"], 100.0 * row["late_FRR"], s=70, color=colors[method])
        axis.annotate(method, (100.0 * row["late_FAR"], 100.0 * row["late_FRR"]), xytext=(6, 5), textcoords="offset points")
    axis.set_xlabel("Late FAR (%)")
    axis.set_ylabel("Late FRR (%)")
    axis.set_title("Day-2 security–adaptation trade-off")
    axis.grid(alpha=0.25)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        path = figure_dir / f"external_temporal_tradeoff.{suffix}"
        fig.savefig(path, dpi=220, bbox_inches="tight")
        created.append(path)
    plt.close(fig)

    trajectory = checkpoints.groupby(["method", "unit"], as_index=False).agg(
        mean=("mean", "mean"),
        threshold=("threshold", "mean"),
        frr=("checkpoint_FRR", "mean"),
        update_rate=("update_event", "mean"),
    )
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True)
    fields = (("mean", "Profile mean"), ("threshold", "Authentication threshold"), ("frr", "Checkpoint FRR"), ("update_rate", "Update rate"))
    for axis, (field, title) in zip(axes.flat, fields):
        for method in METHODS_TEMPORAL:
            line = trajectory[trajectory["method"] == method]
            values = 100.0 * line[field] if field in {"frr", "update_rate"} else line[field]
            axis.plot(line["unit"], values, label=method, color=colors[method])
        axis.set_title(title)
        axis.grid(alpha=0.25)
    axes[1, 0].set_xlabel("Temporal unit")
    axes[1, 1].set_xlabel("Temporal unit")
    axes[0, 1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        path = figure_dir / f"external_selection_bias_trajectory.{suffix}"
        fig.savefig(path, dpi=220, bbox_inches="tight")
        created.append(path)
    plt.close(fig)
    return created


def run_locked_test(
    cache_dir: Path,
    output_dir: Path,
    protocol_path: Path,
    project_dir: Path,
) -> dict:
    protocol = load_protocol(protocol_path)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    cache = load_score_cache(cache_dir, protocol_path)
    attack_rows, exclusions = run_attack_block(cache, protocol)
    checkpoints, temporal_subject = run_temporal_block(cache, protocol)

    numeric_attack = [
        "post_ASR", "FAR", "post_FRR", "HTER", "poison_accept_rate", "MUR",
        "mean_delta", "sigma_delta", "threshold_delta",
    ]
    attack_subject = (
        attack_rows.groupby(["victim", "strategy", "K", "method"], as_index=False)[numeric_attack]
        .mean()
    )
    attack_summary = summarize_absolute(
        attack_subject,
        ["strategy", "K", "method"],
        ["post_ASR", "post_FRR", "HTER", "MUR", "threshold_delta"],
        protocol,
    )
    effects = [
        paired_effect(attack_subject, ["victim"], {"strategy": "boundary", "K": 8}, "post_ASR", "Blind EMA", "Frozen", protocol, "Blind minus Frozen ASR", 10),
        paired_effect(attack_subject, ["victim"], {"strategy": "boundary", "K": 8}, "post_ASR", "Guarded EMA", "Blind EMA", protocol, "Guarded minus Blind ASR", 11),
        paired_effect(attack_subject, ["victim"], {"strategy": "boundary", "K": 8}, "MUR", "Guarded EMA", "Blind EMA", protocol, "Guarded minus Blind MUR", 12),
        paired_effect(attack_subject, ["victim"], {"strategy": "random", "K": 8}, "post_ASR", "Blind EMA", "Frozen", protocol, "Blind minus Frozen ASR (random)", 13),
    ]
    temporal_summary = summarize_absolute(
        temporal_subject,
        ["method"],
        ["early_FRR", "late_FRR", "early_FAR", "late_FAR", "late_HTER", "GUR", "threshold_delta"],
        protocol,
    )
    effects.extend([
        paired_effect(temporal_subject, ["victim"], {}, "late_FRR", "Guarded EMA", "Frozen", protocol, "Guarded minus Frozen late FRR", 20),
        paired_effect(temporal_subject, ["victim"], {}, "late_FRR", "Oracle-all-genuine", "Frozen", protocol, "Oracle-all minus Frozen late FRR", 21),
        paired_effect(temporal_subject, ["victim"], {}, "late_FRR", "Guarded EMA", "Oracle-all-genuine", protocol, "Guarded minus Oracle-all late FRR", 22),
        paired_effect(temporal_subject, ["victim"], {}, "late_FAR", "Oracle-all-genuine", "Guarded EMA", protocol, "Oracle-all minus Guarded late FAR", 23),
    ])
    effect_frame = pd.DataFrame(effects)

    attack_rate_columns = ["post_ASR", "FAR", "post_FRR", "HTER", "poison_accept_rate", "MUR"]
    temporal_rate_columns = ["genuine_auth_rate", "GUR", "early_FRR", "late_FRR", "early_FAR", "late_FAR", "early_HTER", "late_HTER"]
    checkpoint_rate_columns = ["checkpoint_FRR", "checkpoint_FAR"]
    percentage_export(attack_rows, attack_rate_columns).to_csv(output_dir / "attack_subject_repeat.csv", index=False)
    percentage_export(attack_subject, attack_rate_columns).to_csv(output_dir / "attack_by_subject.csv", index=False)
    attack_summary_export = attack_summary.copy()
    rate_mask = attack_summary_export["metric"].isin({"post_ASR", "post_FRR", "HTER", "MUR"})
    attack_summary_export.loc[rate_mask, ["mean", "ci_low", "ci_high"]] *= 100.0
    attack_summary_export.to_csv(output_dir / "attack_summary_bootstrap.csv", index=False)
    percentage_export(checkpoints, checkpoint_rate_columns).to_csv(output_dir / "temporal_checkpoints.csv", index=False)
    percentage_export(temporal_subject, temporal_rate_columns).to_csv(output_dir / "temporal_by_subject.csv", index=False)
    temporal_summary_export = temporal_summary.copy()
    temporal_rate_mask = temporal_summary_export["metric"].isin({"early_FRR", "late_FRR", "early_FAR", "late_FAR", "late_HTER", "GUR"})
    temporal_summary_export.loc[temporal_rate_mask, ["mean", "ci_low", "ci_high"]] *= 100.0
    temporal_summary_export.to_csv(output_dir / "temporal_summary_bootstrap.csv", index=False)
    effect_export = effect_frame.copy()
    effect_rate_mask = effect_export["metric"].isin({"post_ASR", "MUR", "late_FRR", "late_FAR"})
    effect_export.loc[effect_rate_mask, ["mean_effect", "ci_low", "ci_high"]] *= 100.0
    effect_export.to_csv(output_dir / "paired_effects.csv", index=False)
    exclusions.to_csv(output_dir / "exclusions.csv", index=False)

    figure_paths = create_figures(attack_subject, temporal_subject, checkpoints, output_dir)
    conclusions = []
    for _, row in effect_export.iterrows():
        direction = "positive" if row["mean_effect"] > 0 else "negative" if row["mean_effect"] < 0 else "zero"
        conclusions.append({
            "contrast": row["contrast"],
            "mean_effect_pp": row["mean_effect"],
            "ci_low_pp": row["ci_low"],
            "ci_high_pp": row["ci_high"],
            "direction": direction,
            "n_subjects": int(row["n_subjects"]),
        })
    conclusion_frame = pd.DataFrame(conclusions)
    conclusion_frame.to_csv(output_dir / "external_replication_summary.csv", index=False)
    (output_dir / "external_replication_summary.md").write_text(
        conclusion_frame.to_markdown(index=False) + "\n", encoding="utf-8"
    )

    generated = [path for path in output_dir.rglob("*") if path.is_file()]
    manifest = {
        "protocol_id": PROTOCOL_ID,
        "protocol_sha256": sha256_file(protocol_path),
        "created_at": utc_now(),
        "git_revision": git_revision(project_dir),
        "status": "complete",
        "outer_test_loaded": True,
        "tuning_performed": False,
        "score_cache_sha256": sha256_file(cache_dir / "scores_mcgill_day2.npz"),
        "n_attack_subject_repeat_rows": len(attack_rows),
        "n_temporal_subject_rows": len(temporal_subject),
        "n_boundary_exclusions": int(len(exclusions)),
        "generated_files": {str(path.relative_to(output_dir)): sha256_file(path) for path in generated},
        "figures": [str(path.relative_to(output_dir)) for path in figure_paths],
        "environment": environment_snapshot(),
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def run_synthetic_smoke(protocol_path: Path) -> dict:
    protocol = load_protocol(protocol_path)
    enrollment = np.asarray([0.80, 0.82, 0.84, 0.86], dtype=float)
    threshold = 0.70
    poison = np.asarray([0.71, 0.72, 0.73, 0.74], dtype=float)
    probe = np.asarray([0.69, 0.71, 0.75], dtype=float)
    genuine = np.asarray([0.78, 0.81], dtype=float)
    frozen = evaluate_attack_method("Frozen", enrollment, threshold, poison, probe, genuine, protocol)
    blind = evaluate_attack_method("Blind EMA", enrollment, threshold, poison, probe, genuine, protocol)
    guarded = evaluate_attack_method("Guarded EMA", enrollment, threshold, poison, probe, genuine, protocol)
    if frozen["malicious_updates"] != 0:
        raise AssertionError("Frozen updated during smoke test")
    if blind["malicious_updates"] <= guarded["malicious_updates"]:
        raise AssertionError("Synthetic guarded gate did not reduce malicious updates")
    return {
        "status": "passed",
        "frozen_updates": frozen["malicious_updates"],
        "blind_updates": blind["malicious_updates"],
        "guarded_updates": guarded["malicious_updates"],
    }


def build_parser() -> argparse.ArgumentParser:
    project_default = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--protocol",
        type=Path,
        default=project_default / "experiments" / "external_replication_mcgill.json",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path.home() / "Downloads" / "McGillGait" / "gait-dataset",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.home() / "Downloads" / "McGillGait" / "paper3_external_cache_v1",
    )
    subparsers = parser.add_subparsers(dest="stage", required=True)
    subparsers.add_parser("audit")
    subparsers.add_parser("smoke")
    subparsers.add_parser("train")
    subparsers.add_parser("score")
    test_parser = subparsers.add_parser("test")
    test_parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    protocol_path = args.protocol.resolve()
    project_dir = Path(__file__).resolve().parents[1]
    if args.stage == "audit":
        protocol = load_protocol(protocol_path)
        audit, eligible = audit_dataset(args.data_dir.resolve(), protocol)
        args.cache_dir.mkdir(parents=True, exist_ok=True)
        audit.to_csv(args.cache_dir / "dataset_audit.csv", index=False)
        payload = {
            "protocol_id": PROTOCOL_ID,
            "protocol_sha256": sha256_file(protocol_path),
            "created_at": utc_now(),
            "eligible_subjects": eligible,
            "n_eligible": len(eligible),
            "test_scores_computed": False,
        }
        write_json(args.cache_dir / "dataset_audit.json", payload)
        print(json.dumps(payload, indent=2))
        return 0 if len(eligible) == 20 else 2
    if args.stage == "smoke":
        payload = run_synthetic_smoke(protocol_path)
        print(json.dumps(payload, indent=2))
        return 0
    if args.stage == "train":
        payload = run_training(args.data_dir.resolve(), args.cache_dir.resolve(), protocol_path, project_dir)
        print(json.dumps(payload, indent=2))
        return 0
    if args.stage == "score":
        payload = create_score_cache(args.data_dir.resolve(), args.cache_dir.resolve(), protocol_path, project_dir)
        print(json.dumps(payload, indent=2))
        return 0
    if args.stage == "test":
        payload = run_locked_test(args.cache_dir.resolve(), args.output_dir.resolve(), protocol_path, project_dir)
        print(json.dumps(payload, indent=2))
        return 0
    raise AssertionError(args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
