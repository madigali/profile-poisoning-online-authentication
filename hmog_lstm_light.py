# ============================================================
# HMOG — LSTM + Adaptive Agent — DRIFT EXPERIMENT v4
#
# Отвечает на разбор из второго чата:
#
# 1) [FIXED-CALIBRATION PROTOCOL] Главная метрика статьи теперь
#    НЕ bin-wise EER (он абсорбирует то, что агент вообще не
#    может улучшить -- разделимость представления), а способность
#    ДЕРЖАТЬ РАБОЧУЮ ТОЧКУ во времени без переобучения:
#      - статический порог калибруется ТОЛЬКО на early-сегменте
#        (thr_e = EER-порог на early genuine/impostor) и
#        замораживается на late -- FRR/FAR на late без recalibration;
#      - агент идёт по хронологии online со своим адаптивным
#        порогом -- FRR/FAR на late считаются из ЕГО собственных
#        решений в реальном времени.
#      Величина: dFRR = FRR_late - FRR_early. Если агент реально
#      адаптируется -- его dFRR должна расти медленнее, чем у
#      замороженного статического порога.
#
# 2) [EMA В РЕШАЮЩЕМ ПРАВИЛЕ] AdaptiveAgentEMA ведёт EMA-моменты
#    p_t=EMA(s), q_t=EMA(s^2) ТОЛЬКО по принятым (genuine-решённым)
#    попыткам, порог tau_t = p_t - k*sigma_t, где
#    sigma_t = sqrt(max(q_t - p_t^2, 0)). Это делает уравнение
#    статьи (EMA-профиль participates in decision) реально
#    используемым, а не декоративным -- закрывает Reviewer 2 #2
#    по существу, не косметически. Soft-decay к floor при отказах
#    сохранён (из v3), иначе порог замерзает под дрейфом.
#
# 3) [DRIFT SWEEP НА КЕШИРОВАННЫХ МОДЕЛЯХ] Обучение выполняется
#    ОДИН раз на фолд. Дрейф инжектится только в test-признаки
#    после обучения, поэтому весь свип магнитуд {0, 1.5, 2.5, 3.5}
#    считается на одних и тех же обученных моделях -- минуты, не
#    часы. D=0 -- контроль (чистый, недрейфующий тест), даёт
#    "чистый якорь", которого не было в v3 (там "early" уже
#    содержал накопленный дрейф до 0.75*DRIFT_MAX_STD).
#
# 4) [ПРЕДРЕГИСТРИРОВАННЫЙ КРИТЕРИЙ ИСХОДА] Чтобы не подгонять
#    интерпретацию задним числом:
#      УСПЕХ  -> при D=2.5 dFRR_agent < dFRR_static в >=4 из 5
#                фолдов, И разрыв (dFRR_static - dFRR_agent)
#                монотонно растёт к D=3.5.
#      НЕУДАЧА -> честный фрейминг: вклад = temporal-block протокол
#                + честная абляция + первое контролируемое drift-
#                исследование с паритетным/отрицательным результатом.
#
# Bin-wise EER (метод v1-v3) оставлен как ВТОРИЧНАЯ метрика --
# именно она должна показать честный паритет по разделимости,
# в отличие от dFRR, которая должна показать разницу в устойчивости
# рабочей точки, если агент реально работает.
# ============================================================

import os
import warnings
import zipfile
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

from tqdm import tqdm
from scipy.stats import skew
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import accuracy_score

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

np.random.seed(42)
torch.manual_seed(42)

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
    print("[INFO] Используется Apple Silicon GPU (MPS)")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    print("[INFO] Используется CUDA GPU")
else:
    DEVICE = torch.device("cpu")
    print("[INFO] Используется CPU")

# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR      = os.path.expanduser("~/Downloads/public_dataset")
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

# --- AGENT (EMA-профиль, реально участвующий в решении) ---
AGENT_ALPHA_EMA   = 0.05   # скорость EMA для p_t, q_t (моментов)
AGENT_K           = 1.5    # tau_t = p_t - k*sigma_t
AGENT_TAU0        = 0.3    # начальный порог до первой принятой попытки
AGENT_DECAY_RATE  = 0.05   # soft-decay порога при отказах (из v3)
AGENT_FLOOR       = 0.0

# --- DRIFT ---
DRIFT_SWEEP      = [0.0, 1.5, 2.5, 3.5]  # магнитуды в std, 0 = контроль
DRIFT_FEAT_START = 0
DRIFT_FEAT_END   = 18   # accel-признаки (каналы 0-2 * 6 статистик)

# --- SUCCESS CRITERION (предрегистрировано) ---
CRITERION_D_MAIN     = 2.5   # магнитуда, на которой проверяем критерий
CRITERION_MIN_FOLDS  = 4     # dFRR_agent < dFRR_static в >= N из 5 фолдов

ACC_FILENAMES = ["Accelerometer.csv", "accelerometer.csv"]
GYR_FILENAMES = ["Gyroscope.csv",     "gyroscope.csv"]

# ============================================================
# STEP 1: Загрузка данных (без изменений)
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
                        av[:n].astype(float),
                        gv[:n].astype(float)
                    ]))

                    start = 0
                    while start + WINDOW_SIZE <= n:
                        if len(features) >= max_windows:
                            break
                        features.append(extract_features(
                            data[start:start + WINDOW_SIZE]
                        ))
                        start += STEP_SIZE
                except Exception:
                    continue
    except Exception:
        pass
    return features


def load_dataset():
    zip_files = sorted([
        f for f in os.listdir(DATA_DIR) if f.endswith(".zip")
    ])[:MAX_SUBJECTS]

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

# ============================================================
# STEP 2: Последовательности + temporal-block группы
# (порядок внутри субъекта уже хронологический -- критично для
#  агента, дрейфа и fixed-calibration)
# ============================================================

def make_sequences(X_flat, y_flat, n_subjects):
    X_seq, y_seq, groups = [], [], []
    n_dropped = 0
    for sid in range(n_subjects):
        mask   = (y_flat == sid)
        subj_X = X_flat[mask]
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
    print(f"[INFO] Отброшено {n_dropped} sequences, пересекающих "
          f"границы блоков (для устранения train/test overlap)")
    return (np.array(X_seq, dtype=np.float32),
            np.array(y_seq, dtype=np.int64),
            np.array(groups, dtype=np.int64))

# ============================================================
# STEP 3: LSTM модель (без изменений)
# ============================================================

class LSTMAuth(nn.Module):
    def __init__(self, input_size, hidden_size, n_layers,
                 n_classes, dropout):
        super(LSTMAuth, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=n_layers,
            batch_first=True,
            dropout=dropout if n_layers > 1 else 0.0
        )
        self.bn      = nn.BatchNorm1d(hidden_size)
        self.dense   = nn.Linear(hidden_size, 32)
        self.relu    = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.output  = nn.Linear(32, n_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        out    = out[:, -1, :]
        out    = self.bn(out)
        out    = self.relu(self.dense(out))
        out    = self.dropout(out)
        out    = self.output(out)
        return out


def train_epoch(model, loader, optimizer, criterion):
    model.train()
    total_loss, correct, total = 0, 0, 0
    for X_batch, y_batch in loader:
        X_batch = X_batch.to(DEVICE)
        y_batch = y_batch.to(DEVICE)
        optimizer.zero_grad()
        logits = model(X_batch)
        loss   = criterion(logits, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(y_batch)
        correct    += (logits.argmax(1) == y_batch).sum().item()
        total      += len(y_batch)
    return total_loss / total, correct / total


def get_probas(model, X_tensor):
    model.eval()
    all_probas = []
    loader = DataLoader(TensorDataset(X_tensor), batch_size=BATCH_SIZE * 4)
    with torch.no_grad():
        for (X_batch,) in loader:
            logits = model(X_batch.to(DEVICE))
            probas = torch.softmax(logits, dim=1)
            all_probas.append(probas.cpu().numpy())
    return np.vstack(all_probas)

# ============================================================
# STEP 4: Адаптивный Агент v4 -- EMA-профиль в решающем правиле
# ============================================================

class AdaptiveAgentEMA:
    """
    tau_t = p_t - k*sigma_t, где p_t/q_t -- EMA первого/второго
    момента score, обновляемые ТОЛЬКО на попытках, которые сам
    агент классифицировал как genuine (self-training, как вело бы
    себя production-устройство без ground truth). При отказе --
    soft-decay порога к floor (не даёт замерзнуть под дрейфом,
    проблема v2).
    """
    def __init__(self, alpha=AGENT_ALPHA_EMA, k=AGENT_K,
                 init_threshold=AGENT_TAU0,
                 decay_rate=AGENT_DECAY_RATE, floor=AGENT_FLOOR):
        self.alpha      = alpha
        self.k          = k
        self.threshold  = init_threshold
        self.decay_rate = decay_rate
        self.floor      = floor
        self.p = None
        self.q = None

    def decide(self, score):
        margin = score - self.threshold
        is_genuine = margin >= 0
        if is_genuine:
            if self.p is None:
                self.p, self.q = score, score * score
            else:
                self.p = (1 - self.alpha) * self.p + self.alpha * score
                self.q = (1 - self.alpha) * self.q + self.alpha * score * score
            sigma = math.sqrt(max(self.q - self.p ** 2, 0.0))
            self.threshold = max(self.p - self.k * sigma, self.floor)
        else:
            self.threshold = self.threshold - self.decay_rate * (
                self.threshold - self.floor)
        return is_genuine, margin

# ============================================================
# STEP 5: Метрики
# ============================================================

def compute_eer(genuine, impostor):
    all_s      = np.concatenate([genuine, impostor])
    thresholds = np.percentile(all_s, np.linspace(0, 100, 500))
    far = np.array([np.sum(impostor >= t) / max(len(impostor), 1)
                    for t in thresholds])
    frr = np.array([np.sum(genuine  <  t) / max(len(genuine),  1)
                    for t in thresholds])
    idx = np.argmin(np.abs(far - frr))
    eer = (far[idx] + frr[idx]) / 2.0
    return eer, thresholds[idx], far, frr


def _metrics_from_scores(scores, true_bin):
    genuine  = scores[true_bin == 1]
    impostor = scores[true_bin == 0]
    if len(genuine) < 2 or len(impostor) < 2:
        return None
    eer, thr, far, frr = compute_eer(genuine, impostor)
    decisions = (scores >= thr).astype(int)
    acc = accuracy_score(true_bin, decisions)
    return {"EER": eer,
            "FAR": np.sum(impostor >= thr) / max(len(impostor), 1),
            "FRR": np.sum(genuine  <  thr) / max(len(genuine),  1),
            "Accuracy": acc}

# ============================================================
# STEP 6: DRIFT INJECTION
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


def inject_drift(Xte_seq_scaled, drift_frac,
                  max_std,
                  feat_start=DRIFT_FEAT_START,
                  feat_end=DRIFT_FEAT_END,
                  seed=0):
    """max_std=0.0 -> возвращает копию без изменений (контроль D=0)."""
    if max_std == 0.0:
        return Xte_seq_scaled.copy()
    rng = np.random.RandomState(seed)
    n_feat_drift = feat_end - feat_start
    direction = rng.normal(size=n_feat_drift)
    direction = direction / (np.linalg.norm(direction) + 1e-8)

    X_drift = Xte_seq_scaled.copy()
    for i, frac in enumerate(drift_frac):
        shift = direction * (frac * max_std)
        X_drift[i, :, feat_start:feat_end] += shift[None, :]
    return X_drift

# ============================================================
# STEP 7: Оценка -- bin-wise EER (вторичная) + fixed-calibration
#         dFRR (главная метрика)
# ============================================================

def run_agent_full_sequence(scores, order_idx):
    """
    Прогоняет AdaptiveAgentEMA по хронологии субъекта (order_idx).
    Возвращает decisions (bool) и margins в ИСХОДНОМ порядке scores
    (не хронологическом), чтобы совмещать с true_bin/drift_frac масками.
    """
    agent = AdaptiveAgentEMA()
    decisions = np.zeros(len(scores), dtype=bool)
    margins   = np.zeros(len(scores), dtype=np.float64)
    for idx in order_idx:
        is_g, margin = agent.decide(float(scores[idx]))
        decisions[idx] = is_g
        margins[idx]   = margin
    return decisions, margins


def evaluate_fold_at_drift(probas_D, yte_np, drift_frac, te_groups):
    """
    Для одного (fold, drift magnitude D):
      - bin-wise EER early/late, пул по всем субъектам фолда
        (LSTM-only raw scores vs Agent margins) -- ВТОРИЧНАЯ метрика.
      - fixed-calibration dFRR по каждому субъекту, затем усреднение
        по субъектам фолда -- ГЛАВНАЯ метрика.
    """
    subj_ids   = te_groups // 100000
    early_mask = drift_frac < 0.5
    late_mask  = ~early_mask

    # --- bin-wise EER (пул по субъектам) ---
    raw_eg, raw_ei, raw_lg, raw_li = [], [], [], []
    agt_eg, agt_ei, agt_lg, agt_li = [], [], [], []

    # --- fixed-calibration dFRR (по субъектам, затем среднее) ---
    static_frr_early, static_frr_late, static_far_late = [], [], []
    agent_frr_early,  agent_frr_late,  agent_far_late  = [], [], []

    subjects = [s for s in np.unique(yte_np) if s in np.unique(subj_ids)]

    for sid in subjects:
        scores   = probas_D[:, sid]
        true_bin = (yte_np == sid).astype(int)
        order    = np.argsort(drift_frac, kind="stable")

        decisions, margins = run_agent_full_sequence(scores, order)

        g_e_mask = early_mask & (true_bin == 1)
        i_e_mask = early_mask & (true_bin == 0)
        g_l_mask = late_mask  & (true_bin == 1)
        i_l_mask = late_mask  & (true_bin == 0)

        # bin-wise EER pools
        raw_eg.append(scores[g_e_mask]);  raw_ei.append(scores[i_e_mask])
        raw_lg.append(scores[g_l_mask]);  raw_li.append(scores[i_l_mask])
        agt_eg.append(margins[g_e_mask]); agt_ei.append(margins[i_e_mask])
        agt_lg.append(margins[g_l_mask]); agt_li.append(margins[i_l_mask])

        # --- fixed-calibration protocol ---
        g_early, i_early = scores[g_e_mask], scores[i_e_mask]
        g_late,  i_late  = scores[g_l_mask], scores[i_l_mask]
        if len(g_early) >= 2 and len(i_early) >= 2 and \
           len(g_late)  >= 1 and len(i_late)  >= 1:
            _, thr_e, _, _ = compute_eer(g_early, i_early)
            frr_e = np.mean(g_early < thr_e)
            frr_l = np.mean(g_late  < thr_e)
            far_l = np.mean(i_late  >= thr_e)
            static_frr_early.append(frr_e)
            static_frr_late.append(frr_l)
            static_far_late.append(far_l)

        if g_e_mask.sum() >= 1 and g_l_mask.sum() >= 1:
            frr_e_agent = np.mean(~decisions[g_e_mask])
            frr_l_agent = np.mean(~decisions[g_l_mask])
            far_l_agent = (np.mean(decisions[i_l_mask])
                           if i_l_mask.sum() >= 1 else np.nan)
            agent_frr_early.append(frr_e_agent)
            agent_frr_late.append(frr_l_agent)
            agent_far_late.append(far_l_agent)

    def pool_eer(g_list, i_list):
        g = np.concatenate(g_list) if g_list else np.array([])
        i = np.concatenate(i_list) if i_list else np.array([])
        if len(g) < 2 or len(i) < 2:
            return None
        return _metrics_from_scores(np.concatenate([g, i]),
                                     np.concatenate([np.ones(len(g)),
                                                      np.zeros(len(i))]))

    bin_eer = {
        "LSTM-only_early": pool_eer(raw_eg, raw_ei),
        "LSTM-only_late":  pool_eer(raw_lg, raw_li),
        "Agent_early":     pool_eer(agt_eg, agt_ei),
        "Agent_late":      pool_eer(agt_lg, agt_li),
    }

    def nanmean(lst):
        return float(np.nanmean(lst)) if len(lst) else np.nan

    fixed_cal = {
        "static_FRR_early": nanmean(static_frr_early),
        "static_FRR_late":  nanmean(static_frr_late),
        "static_FAR_late":  nanmean(static_far_late),
        "agent_FRR_early":  nanmean(agent_frr_early),
        "agent_FRR_late":   nanmean(agent_frr_late),
        "agent_FAR_late":   nanmean(agent_far_late),
    }
    fixed_cal["dFRR_static"] = (fixed_cal["static_FRR_late"]
                                 - fixed_cal["static_FRR_early"])
    fixed_cal["dFRR_agent"]  = (fixed_cal["agent_FRR_late"]
                                 - fixed_cal["agent_FRR_early"])

    return bin_eer, fixed_cal

# ============================================================
# STEP 8: Главный pipeline
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("HMOG — LSTM (+/- Adaptive Agent) — DRIFT SWEEP v4")
    print(f"Device: {DEVICE}  |  DRIFT_SWEEP={DRIFT_SWEEP}")
    print("=" * 60)

    if not os.path.exists(DATA_DIR):
        print(f"[ERROR] Папка не найдена: {DATA_DIR}")
        exit(1)

    X_flat, y_flat, n_subjects = load_dataset()

    print(f"\n[INFO] Создаём последовательности (seq_len={SEQ_LEN})...")
    X_seq_raw, y_seq, groups = make_sequences(X_flat, y_flat, n_subjects)
    print(f"[INFO] X_seq: {X_seq_raw.shape}, "
          f"temporal-блоков: {len(np.unique(groups))}")

    n_features = X_seq_raw.shape[2]
    gkf = GroupKFold(n_splits=5)

    # all_rows: список dict-строк для итогового CSV
    # (fold, D, bin_eer.*, fixed_cal.*)
    all_rows = []

    for fold, (tr, te) in enumerate(
            gkf.split(X_seq_raw, y_seq, groups=groups), 1):
        print(f"\n[INFO] === Fold {fold}/5 (обучение один раз) ===")

        Xtr_raw, Xte_raw = X_seq_raw[tr], X_seq_raw[te]
        n_tr, sl, nf = Xtr_raw.shape
        n_te         = Xte_raw.shape[0]

        scaler = StandardScaler()
        scaler.fit(Xtr_raw.reshape(-1, nf))
        Xtr_seq = np.nan_to_num(scaler.transform(
            Xtr_raw.reshape(-1, nf)).reshape(n_tr, sl, nf).astype(np.float32))
        Xte_seq = np.nan_to_num(scaler.transform(
            Xte_raw.reshape(-1, nf)).reshape(n_te, sl, nf).astype(np.float32))

        Xtr = torch.tensor(Xtr_seq, dtype=torch.float32)
        ytr = torch.tensor(y_seq[tr], dtype=torch.long)
        yte_np = y_seq[te]
        te_groups = groups[te]

        train_loader = DataLoader(TensorDataset(Xtr, ytr),
                                   batch_size=BATCH_SIZE, shuffle=True)
        val_size = max(1, len(Xtr) // 10)
        val_X = Xtr[-val_size:].to(DEVICE)
        val_y = ytr[-val_size:].to(DEVICE)

        model = LSTMAuth(n_features, LSTM_HIDDEN, LSTM_LAYERS,
                          n_subjects, DROPOUT).to(DEVICE)
        optimizer = optim.Adam(model.parameters(), lr=LR)
        criterion = nn.CrossEntropyLoss()
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, factor=0.5, patience=3)

        best_val_loss, best_state, patience_count = float("inf"), None, 0

        for epoch in range(1, EPOCHS + 1):
            tr_loss, tr_acc = train_epoch(model, train_loader,
                                           optimizer, criterion)
            model.eval()
            with torch.no_grad():
                val_logits = model(val_X)
                v_loss = criterion(val_logits, val_y).item()
                v_acc  = (val_logits.argmax(1) == val_y).float().mean().item()
            scheduler.step(v_loss)
            print(f"  Epoch {epoch:2d}/{EPOCHS} | Loss: {tr_loss:.4f} | "
                  f"Acc: {tr_acc:.3f} | Val Loss: {v_loss:.4f} | "
                  f"Val Acc: {v_acc:.3f}")
            if v_loss < best_val_loss:
                best_val_loss = v_loss
                best_state = {k: v.clone()
                              for k, v in model.state_dict().items()}
                patience_count = 0
            else:
                patience_count += 1
                if patience_count >= PATIENCE:
                    print(f"  [Early stopping at epoch {epoch}]")
                    break

        model.load_state_dict(best_state)

        # --- КЕШИРУЕМ: drift_frac не зависит от магнитуды, считаем 1 раз ---
        drift_frac = compute_drift_fraction(te_groups)

        # --- SWEEP по магнитудам на одной обученной модели ---
        print(f"\n[INFO] Свип дрейфа {DRIFT_SWEEP} на кешированной модели...")
        for D in DRIFT_SWEEP:
            Xte_D = inject_drift(Xte_seq, drift_frac, max_std=D)
            X_te_tensor = torch.tensor(Xte_D, dtype=torch.float32)
            probas_D = get_probas(model, X_te_tensor)

            bin_eer, fixed_cal = evaluate_fold_at_drift(
                probas_D, yte_np, drift_frac, te_groups)

            def eer_pct(d, key):
                return d[key]["EER"] * 100 if d.get(key) else np.nan

            row = {
                "fold": fold, "D": D,
                "bin_EER_lstm_early": eer_pct(bin_eer, "LSTM-only_early"),
                "bin_EER_lstm_late":  eer_pct(bin_eer, "LSTM-only_late"),
                "bin_EER_agent_early": eer_pct(bin_eer, "Agent_early"),
                "bin_EER_agent_late":  eer_pct(bin_eer, "Agent_late"),
                "static_FRR_early": fixed_cal["static_FRR_early"] * 100,
                "static_FRR_late":  fixed_cal["static_FRR_late"] * 100,
                "static_FAR_late":  fixed_cal["static_FAR_late"] * 100,
                "agent_FRR_early":  fixed_cal["agent_FRR_early"] * 100,
                "agent_FRR_late":   fixed_cal["agent_FRR_late"] * 100,
                "agent_FAR_late":   fixed_cal["agent_FAR_late"] * 100,
                "dFRR_static": fixed_cal["dFRR_static"] * 100,
                "dFRR_agent":  fixed_cal["dFRR_agent"] * 100,
            }
            all_rows.append(row)

            print(f"  D={D:>4.1f} | dFRR_static={row['dFRR_static']:+6.2f}п.п. "
                  f"| dFRR_agent={row['dFRR_agent']:+6.2f}п.п. "
                  f"| bin-EER late (LSTM/Agent)="
                  f"{row['bin_EER_lstm_late']:.2f}%/{row['bin_EER_agent_late']:.2f}%")

        del model
        if DEVICE.type == "mps":
            torch.mps.empty_cache()
        elif DEVICE.type == "cuda":
            torch.cuda.empty_cache()

    # ============================================================
    # Итог: сохранение + проверка предрегистрированного критерия
    # ============================================================

    df = pd.DataFrame(all_rows)
    df.to_csv("hmog_drift_sweep_results.csv", index=False)
    print("\n[INFO] Сохранено: hmog_drift_sweep_results.csv (per-fold, per-D)")

    print("\n" + "=" * 60)
    print("ИТОГ ПО МАГНИТУДАМ (среднее по 5 фолдам)")
    print("=" * 60)
    summary = df.groupby("D")[["dFRR_static", "dFRR_agent",
                                "bin_EER_lstm_late",
                                "bin_EER_agent_late"]].mean()
    print(summary.round(2))
    summary.to_csv("hmog_drift_sweep_summary.csv")

    # --- Проверка предрегистрированного критерия успеха ---
    d_main = df[df["D"] == CRITERION_D_MAIN]
    n_folds_agent_better = int((d_main["dFRR_agent"]
                                 < d_main["dFRR_static"]).sum())

    gap_by_D = (df.groupby("D")
                  .apply(lambda g: (g["dFRR_static"] - g["dFRR_agent"]).mean()))
    sweep_sorted = sorted(DRIFT_SWEEP)
    gaps_nonzero = [gap_by_D[d] for d in sweep_sorted if d > 0]
    monotonic = all(gaps_nonzero[i] <= gaps_nonzero[i + 1]
                     for i in range(len(gaps_nonzero) - 1))

    print(f"\n[КРИТЕРИЙ УСПЕХА, D={CRITERION_D_MAIN}]")
    print(f"  dFRR_agent < dFRR_static в {n_folds_agent_better}/5 фолдов "
          f"(нужно >= {CRITERION_MIN_FOLDS})")
    print(f"  Разрыв (static-agent) по магнитудам: "
          f"{dict(zip(sweep_sorted, [round(g,2) for g in gap_by_D[sweep_sorted]]))}")
    print(f"  Монотонный рост разрыва {sweep_sorted[1:]}: {monotonic}")

    success = (n_folds_agent_better >= CRITERION_MIN_FOLDS) and monotonic
    if success:
        print("\n  [РЕЗУЛЬТАТ] УСПЕХ -- агент сохраняет рабочую точку (FRR) "
              "под дрейфом лучше статического порога, разрыв растёт с "
              "магнитудой. Можно писать как содержательный результат.")
    else:
        print("\n  [РЕЗУЛЬТАТ] Критерий не выполнен -- честный фрейминг: "
              "temporal-block протокол + честная абляция + первое "
              "контролируемое drift-исследование с паритетным/"
              "отрицательным результатом, без свипа в заголовке.")

    # --- График: dFRR vs magnitude ---
    plt.figure(figsize=(7, 5))
    plt.plot(summary.index, summary["dFRR_static"], "o-",
             color="purple", label="Static (frozen threshold)")
    plt.plot(summary.index, summary["dFRR_agent"], "o-",
             color="green", label="Adaptive Agent (EMA)")
    plt.xlabel("Магнитуда дрейфа (σ)")
    plt.ylabel("ΔFRR = FRR(late) − FRR(early), п.п.")
    plt.title("Устойчивость рабочей точки под дрейфом")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("hmog_drift_sweep_dFRR.png", dpi=150)
    print("\n[INFO] График: hmog_drift_sweep_dFRR.png")

    # --- График: bin-wise EER (вторичная метрика, честный паритет) ---
    plt.figure(figsize=(7, 5))
    plt.plot(summary.index, summary["bin_EER_lstm_late"], "o--",
             color="purple", label="LSTM-only (bin-wise EER, late)")
    plt.plot(summary.index, summary["bin_EER_agent_late"], "o--",
             color="green", label="Agent (bin-wise EER, late)")
    plt.xlabel("Магнитуда дрейфа (σ)")
    plt.ylabel("EER (%), late-сегмент")
    plt.title("Разделимость под дрейфом (вторичная метрика)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("hmog_drift_sweep_bin_EER.png", dpi=150)
    print("[INFO] График: hmog_drift_sweep_bin_EER.png")

    print("\n[ГОТОВО] Drift sweep v4 завершён.")