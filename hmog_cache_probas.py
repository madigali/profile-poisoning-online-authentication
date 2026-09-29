# ============================================================
# hmog_cache_probas.py  —  ДОРОГОЙ ПРОГОН, ОДИН РАЗ
#
# Обучает 5 fold-моделей (leakage-free temporal-block протокол),
# инжектит дрейф каждой магнитуды и СОХРАНЯЕТ на диск:
#   probas[fold][D], yte, te_groups, drift_frac
#
# После этого все анализы (ablation, OP-кривая, matched-OP,
# floor-sensitivity) считаются из кеша за секунды скриптом
# hmog_analysis.py, без переобучения.
#
# Кеш: ./cache_probas/fold{F}_D{D}.npz  (~7 МБ суммарно)
# ============================================================

import os
import math
import warnings
import zipfile
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from tqdm import tqdm
from scipy.stats import skew
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

np.random.seed(42)
torch.manual_seed(42)

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
    print("[INFO] Apple Silicon GPU (MPS)")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    print("[INFO] CUDA GPU")
else:
    DEVICE = torch.device("cpu")
    print("[INFO] CPU")

# ============================================================
# CONFIG  (идентичен hmog_lstm_light.py v4)
# ============================================================

DATA_DIR = os.path.expanduser("~/Downloads/hmog_dataset/public_dataset")
if not os.path.exists(DATA_DIR):
    DATA_DIR = os.path.expanduser("~/Downloads/public_dataset")

CACHE_DIR    = "cache_probas"

WINDOW_SIZE  = 100
STEP_SIZE    = 100
MAX_SUBJECTS = 100
MAX_WINDOWS  = 300
SEQ_LEN      = 20
SEQ_STEP     = 5
BLOCK_SIZE   = 60

LSTM_HIDDEN  = 128
LSTM_LAYERS  = 2
DROPOUT      = 0.3
BATCH_SIZE   = 32
EPOCHS       = 50
LR           = 0.001
PATIENCE     = 5

DRIFT_SWEEP      = [0.0, 1.5, 2.5, 3.5]
DRIFT_FEAT_START = 0
DRIFT_FEAT_END   = 36

ACC_FILENAMES = ["Accelerometer.csv", "accelerometer.csv"]
GYR_FILENAMES = ["Gyroscope.csv",     "gyroscope.csv"]

# ============================================================
# Загрузка (идентична основному скрипту)
# ============================================================

def find_sensor_files(file_list):
    sessions = {}
    for fname in file_list:
        basename = os.path.basename(fname).lower()
        dirname  = os.path.dirname(fname)
        for a in ACC_FILENAMES:
            if basename == a.lower():
                sessions.setdefault(dirname, {"acc": None, "gyr": None})
                sessions[dirname]["acc"] = fname
        for g in GYR_FILENAMES:
            if basename == g.lower():
                sessions.setdefault(dirname, {"acc": None, "gyr": None})
                sessions[dirname]["gyr"] = fname
    return {k: v for k, v in sessions.items() if v["acc"] and v["gyr"]}


def extract_features(window):
    features = []
    for ch in range(window.shape[1]):
        col = window[:, ch].astype(float)
        features.append(np.mean(col))
        features.append(np.std(col))
        features.append(np.min(col))
        features.append(np.max(col))
        features.append(np.sqrt(np.mean(col ** 2)))
        features.append(float(skew(col)) if np.std(col) > 0 else 0.0)
    return features


def load_subject(zip_path, max_windows=MAX_WINDOWS):
    features = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            sessions = find_sensor_files(zf.namelist())
            for _, paths in sessions.items():
                if len(features) >= max_windows:
                    break
                try:
                    with zf.open(paths["acc"]) as f:
                        acc = pd.read_csv(f, header=None)
                    with zf.open(paths["gyr"]) as f:
                        gyr = pd.read_csv(f, header=None)
                    av = acc.iloc[:, 1:4].values if acc.shape[1] >= 4 \
                         else acc.iloc[:, :3].values
                    gv = gyr.iloc[:, 1:4].values if gyr.shape[1] >= 4 \
                         else gyr.iloc[:, :3].values
                    n = min(len(av), len(gv))
                    if n < WINDOW_SIZE:
                        continue
                    data = np.nan_to_num(np.hstack([
                        av[:n].astype(float), gv[:n].astype(float)]))
                    start = 0
                    while start + WINDOW_SIZE <= n:
                        if len(features) >= max_windows:
                            break
                        features.append(extract_features(
                            data[start:start + WINDOW_SIZE]))
                        start += STEP_SIZE
                except Exception:
                    continue
    except Exception:
        pass
    return features


def load_dataset():
    zip_files = sorted([f for f in os.listdir(DATA_DIR)
                        if f.endswith(".zip")])[:MAX_SUBJECTS]
    print(f"[INFO] Загружаем {len(zip_files)} субъектов...")
    all_X, all_y = [], []
    valid = 0
    for zf in tqdm(zip_files, desc="Загрузка"):
        feats = load_subject(os.path.join(DATA_DIR, zf))
        if len(feats) >= SEQ_LEN + 2:
            all_X.extend(feats)
            all_y.extend([valid] * len(feats))
            valid += 1
    print(f"[INFO] Субъектов: {valid}, Окон: {len(all_X)}")
    return (np.nan_to_num(np.array(all_X, dtype=float)),
            np.array(all_y), valid)


def make_sequences(X_flat, y_flat, n_subjects):
    X_seq, y_seq, groups = [], [], []
    n_dropped = 0
    for sid in range(n_subjects):
        subj_X = X_flat[y_flat == sid]
        start  = 0
        while start + SEQ_LEN <= len(subj_X):
            b_start = start // BLOCK_SIZE
            b_end   = (start + SEQ_LEN - 1) // BLOCK_SIZE
            if b_start == b_end:
                X_seq.append(subj_X[start:start + SEQ_LEN])
                y_seq.append(sid)
                groups.append(sid * 100000 + b_start)
            else:
                n_dropped += 1
            start += SEQ_STEP
    print(f"[INFO] Отброшено {n_dropped} граничных sequences")
    return (np.array(X_seq, dtype=np.float32),
            np.array(y_seq, dtype=np.int64),
            np.array(groups, dtype=np.int64))

# ============================================================
# Модель
# ============================================================

class LSTMAuth(nn.Module):
    def __init__(self, input_size, hidden_size, n_layers,
                 n_classes, dropout):
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size,
                            num_layers=n_layers, batch_first=True,
                            dropout=dropout if n_layers > 1 else 0.0)
        self.bn      = nn.BatchNorm1d(hidden_size)
        self.dense   = nn.Linear(hidden_size, 32)
        self.relu    = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.output  = nn.Linear(32, n_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.bn(out)
        out = self.relu(self.dense(out))
        out = self.dropout(out)
        return self.output(out)


def train_epoch(model, loader, optimizer, criterion):
    model.train()
    total_loss, correct, total = 0, 0, 0
    for Xb, yb in loader:
        Xb, yb = Xb.to(DEVICE), yb.to(DEVICE)
        optimizer.zero_grad()
        logits = model(Xb)
        loss = criterion(logits, yb)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(yb)
        correct += (logits.argmax(1) == yb).sum().item()
        total += len(yb)
    return total_loss / total, correct / total


def get_probas(model, X_tensor):
    model.eval()
    out = []
    loader = DataLoader(TensorDataset(X_tensor), batch_size=BATCH_SIZE * 4)
    with torch.no_grad():
        for (Xb,) in loader:
            out.append(torch.softmax(model(Xb.to(DEVICE)), dim=1).cpu().numpy())
    return np.vstack(out)

# ============================================================
# Дрейф
# ============================================================

def compute_drift_fraction(te_groups):
    subj_ids  = te_groups // 100000
    block_ids = te_groups % 100000
    frac = np.zeros(len(te_groups), dtype=np.float32)
    for sid in np.unique(subj_ids):
        idxs  = np.where(subj_ids == sid)[0]
        order = idxs[np.argsort(block_ids[idxs], kind="stable")]
        n = len(order)
        for rank, idx in enumerate(order):
            frac[idx] = rank / max(n - 1, 1)
    return frac


def inject_drift(X, drift_frac, max_std,
                 feat_start=DRIFT_FEAT_START, feat_end=DRIFT_FEAT_END, seed=0):
    if max_std == 0.0:
        return X.copy()
    rng = np.random.RandomState(seed)
    d = rng.normal(size=feat_end - feat_start)
    d = d / (np.linalg.norm(d) + 1e-8)
    Xd = X.copy()
    for i, frac in enumerate(drift_frac):
        Xd[i, :, feat_start:feat_end] += (d * (frac * max_std))[None, :]
    return Xd

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("КЕШИРОВАНИЕ PROBAS — дорогой прогон, один раз")
    print("=" * 60)

    if not os.path.exists(DATA_DIR):
        print(f"[ERROR] Не найдена папка: {DATA_DIR}")
        exit(1)

    os.makedirs(CACHE_DIR, exist_ok=True)

    X_flat, y_flat, n_subjects = load_dataset()
    X_seq_raw, y_seq, groups = make_sequences(X_flat, y_flat, n_subjects)
    print(f"[INFO] X_seq: {X_seq_raw.shape}, блоков: {len(np.unique(groups))}")

    n_features = X_seq_raw.shape[2]
    gkf = GroupKFold(n_splits=5)

    for fold, (tr, te) in enumerate(gkf.split(X_seq_raw, y_seq, groups=groups), 1):
        print(f"\n[INFO] === Fold {fold}/5 ===")

        Xtr_raw, Xte_raw = X_seq_raw[tr], X_seq_raw[te]
        n_tr, sl, nf = Xtr_raw.shape
        n_te = Xte_raw.shape[0]

        scaler = StandardScaler()
        scaler.fit(Xtr_raw.reshape(-1, nf))
        Xtr_seq = np.nan_to_num(scaler.transform(
            Xtr_raw.reshape(-1, nf)).reshape(n_tr, sl, nf).astype(np.float32))
        Xte_seq = np.nan_to_num(scaler.transform(
            Xte_raw.reshape(-1, nf)).reshape(n_te, sl, nf).astype(np.float32))

        Xtr = torch.tensor(Xtr_seq, dtype=torch.float32)
        ytr = torch.tensor(y_seq[tr], dtype=torch.long)
        yte_np    = y_seq[te]
        te_groups = groups[te]

        loader = DataLoader(TensorDataset(Xtr, ytr),
                            batch_size=BATCH_SIZE, shuffle=True)
        val_size = max(1, len(Xtr) // 10)
        val_X = Xtr[-val_size:].to(DEVICE)
        val_y = ytr[-val_size:].to(DEVICE)

        model = LSTMAuth(n_features, LSTM_HIDDEN, LSTM_LAYERS,
                         n_subjects, DROPOUT).to(DEVICE)
        optimizer = optim.Adam(model.parameters(), lr=LR)
        criterion = nn.CrossEntropyLoss()
        sched = optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=0.5,
                                                      patience=3)

        best, best_state, wait = float("inf"), None, 0
        for epoch in range(1, EPOCHS + 1):
            tr_loss, tr_acc = train_epoch(model, loader, optimizer, criterion)
            model.eval()
            with torch.no_grad():
                v_loss = criterion(model(val_X), val_y).item()
            sched.step(v_loss)
            print(f"  Epoch {epoch:2d}/{EPOCHS} | Loss {tr_loss:.4f} | "
                  f"Val {v_loss:.4f}")
            if v_loss < best:
                best, wait = v_loss, 0
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
            else:
                wait += 1
                if wait >= PATIENCE:
                    print(f"  [Early stopping @ {epoch}]")
                    break
        model.load_state_dict(best_state)

        drift_frac = compute_drift_fraction(te_groups)

        for D in DRIFT_SWEEP:
            Xte_D = inject_drift(Xte_seq, drift_frac, max_std=D)
            probas = get_probas(model, torch.tensor(Xte_D, dtype=torch.float32))
            path = os.path.join(CACHE_DIR, f"fold{fold}_D{D}.npz")
            np.savez_compressed(path,
                                probas=probas.astype(np.float32),
                                yte=yte_np,
                                te_groups=te_groups,
                                drift_frac=drift_frac)
            print(f"  [CACHE] D={D}: {path}  probas={probas.shape}")

        del model
        if DEVICE.type == "mps":
            torch.mps.empty_cache()
        elif DEVICE.type == "cuda":
            torch.cuda.empty_cache()

    total_mb = sum(os.path.getsize(os.path.join(CACHE_DIR, f))
                   for f in os.listdir(CACHE_DIR)) / 1e6
    print(f"\n[ГОТОВО] Кеш записан в ./{CACHE_DIR}/ ({total_mb:.1f} МБ)")
    print("[СЛЕДУЮЩИЙ ШАГ] python hmog_analysis.py")