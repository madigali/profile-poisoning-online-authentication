# ============================================================
# HMOG Baseline (SVM + RF) — v3
#
# ИСПРАВЛЕНИЯ v3 -- протокол теперь ИДЕНТИЧЕН тому, что
# используется в hmog_lstm_light.py v3, чтобы сравнение
# SVM / RF / LSTM в таблице было корректным:
#
#   1) [NO LEAKAGE] StandardScaler фитится ТОЛЬКО на train-
#      фолде (раньше был fit_transform на всём X до
#      разбиения -- тестовые данные утекали в статистику
#      нормализации).
#   2) [TEMPORAL SPLIT] GroupKFold по тем же temporal-блокам
#      (BLOCK_SIZE=60 окон), что и в LSTM-скрипте, вместо
#      случайного StratifiedKFold. Без этого baseline'ы
#      получали бы преимущество от утечки, которую у LSTM
#      уже устранили.
#
# ВАЖНО: запускать ПЕРЕД hmog_lstm_light.py -- тот читает
# hmog_baseline_results.csv для итоговой сводной таблицы.
# ============================================================

import os
import warnings
import zipfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

from tqdm import tqdm
from scipy.stats import skew
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import accuracy_score

# ============================================================
# CONFIGURATION
# ============================================================

# Путь: работает и на Mac (~/Downloads/...), и на Windows,
# если папка лежит в Downloads. При необходимости поправьте.
DATA_DIR      = os.path.expanduser("~/Downloads/hmog_dataset/public_dataset")
if not os.path.exists(DATA_DIR):
    # запасной вариант -- старая структура папок
    DATA_DIR = os.path.expanduser("~/Downloads/public_dataset")

WINDOW_SIZE   = 100
STEP_SIZE     = 100   # Без перекрытия — окна независимы
N_FOLDS       = 5
MAX_SUBJECTS  = 100
MAX_WINDOWS   = 300

# Тот же размер temporal-блока, что и в hmog_lstm_light.py v3.
# Обеспечивает одинаковое разбиение данных для всех моделей.
BLOCK_SIZE    = 60

ACC_FILENAMES = ["Accelerometer.csv", "accelerometer.csv"]
GYR_FILENAMES = ["Gyroscope.csv",     "gyroscope.csv"]

# ============================================================
# Загрузка данных
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
    """
    Возвращает X, y и groups. groups = (subject_id, block_index),
    где block_index = window_index // BLOCK_SIZE -- те же
    temporal-блоки, что использует LSTM-скрипт.
    """
    zip_files = sorted([
        f for f in os.listdir(DATA_DIR) if f.endswith(".zip")
    ])[:MAX_SUBJECTS]

    print(f"[INFO] Загружаем {len(zip_files)} субъектов "
          f"(макс. {MAX_WINDOWS} окон, шаг {STEP_SIZE})...")

    all_X, all_y, all_g = [], [], []
    valid = 0
    for zf in tqdm(zip_files, desc="Загрузка"):
        feats = load_subject(os.path.join(DATA_DIR, zf))
        if len(feats) >= 10:
            all_X.extend(feats)
            all_y.extend([valid] * len(feats))
            # индекс окна внутри субъекта -> номер блока
            all_g.extend([valid * 100000 + (w // BLOCK_SIZE)
                          for w in range(len(feats))])
            valid += 1

    print(f"[INFO] Субъектов: {valid}, Окон: {len(all_X)}, "
          f"temporal-блоков: {len(set(all_g))}")
    return (np.nan_to_num(np.array(all_X, dtype=float)),
            np.array(all_y),
            np.array(all_g))

# ============================================================
# Метрики
# ============================================================

def compute_eer(genuine, impostor):
    all_scores = np.concatenate([genuine, impostor])
    thresholds = np.percentile(all_scores, np.linspace(0, 100, 500))

    far_list, frr_list = [], []
    for t in thresholds:
        far_list.append(np.sum(impostor >= t) / max(len(impostor), 1))
        frr_list.append(np.sum(genuine < t)  / max(len(genuine),  1))

    far = np.array(far_list)
    frr = np.array(frr_list)
    idx = np.argmin(np.abs(far - frr))
    eer = (far[idx] + frr[idx]) / 2.0
    return eer, thresholds[idx], far, frr, thresholds


def evaluate_model(model, X_test, y_test, subj_id):
    """Оценка одного субъекта (one-vs-all) по вероятностным scores."""
    classes = list(model.classes_)
    if subj_id not in classes:
        return None
    cidx = classes.index(subj_id)

    proba    = model.predict_proba(X_test)
    scores   = proba[:, cidx]
    true_bin = (y_test == subj_id).astype(int)

    genuine  = scores[true_bin == 1]
    impostor = scores[true_bin == 0]
    if len(genuine) < 2 or len(impostor) < 2:
        return None

    eer, thr, far, frr, thresholds = compute_eer(genuine, impostor)
    decisions = (scores >= thr).astype(int)
    bin_acc   = accuracy_score(true_bin, decisions)

    return {
        "EER":      eer,
        "FAR":      np.sum(impostor >= thr) / max(len(impostor), 1),
        "FRR":      np.sum(genuine  <  thr) / max(len(genuine),  1),
        "Accuracy": bin_acc,
        "far": far, "frr": frr, "thresholds": thresholds
    }

# ============================================================
# Главный pipeline
# ============================================================

if __name__ == "__main__":

    print("=" * 55)
    print("HMOG Baseline v3 (no leakage + temporal-block split)")
    print(f"Субъектов: {MAX_SUBJECTS} | Окон: {MAX_WINDOWS} | "
          f"Блок: {BLOCK_SIZE}")
    print("=" * 55)

    if not os.path.exists(DATA_DIR):
        print(f"[ERROR] Не найдена папка: {DATA_DIR}")
        print("Поправьте DATA_DIR в начале файла.")
        exit(1)

    X, y, groups = load_dataset()
    # ВАЖНО: scaler.fit_transform(X) здесь НЕ вызывается --
    # нормализация теперь внутри цикла по фолдам.

    gkf = GroupKFold(n_splits=N_FOLDS)

    results = {
        "SVM":          {"EER": [], "FAR": [], "FRR": [], "Accuracy": []},
        "RandomForest": {"EER": [], "FAR": [], "FRR": [], "Accuracy": []}
    }

    last_svm_res = None
    last_rf_res  = None

    for fold, (tr, te) in enumerate(gkf.split(X, y, groups=groups), 1):
        print(f"\n[INFO] === Fold {fold}/{N_FOLDS} ===")
        Xtr_raw, Xte_raw = X[tr], X[te]
        ytr, yte = y[tr], y[te]

        # --- Нормализация: fit ТОЛЬКО на train ---
        scaler = StandardScaler()
        Xtr = scaler.fit_transform(Xtr_raw)
        Xte = scaler.transform(Xte_raw)

        print("[INFO]   SVM (Linear)...")
        svm = CalibratedClassifierCV(
            LinearSVC(C=1.0, max_iter=2000, random_state=42), cv=3
        )
        svm.fit(Xtr, ytr)

        print("[INFO]   Random Forest...")
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_leaf=8,
            min_samples_split=15,
            max_features="sqrt",
            n_jobs=-1,
            random_state=42
        )
        rf.fit(Xtr, ytr)

        svm_fold = {"EER": [], "FAR": [], "FRR": [], "Accuracy": []}
        rf_fold  = {"EER": [], "FAR": [], "FRR": [], "Accuracy": []}

        for sid in np.unique(yte):
            r1 = evaluate_model(svm, Xte, yte, sid)
            r2 = evaluate_model(rf,  Xte, yte, sid)
            if r1:
                for m in ["EER","FAR","FRR","Accuracy"]:
                    svm_fold[m].append(r1[m])
                last_svm_res = r1
            if r2:
                for m in ["EER","FAR","FRR","Accuracy"]:
                    rf_fold[m].append(r2[m])
                last_rf_res = r2

        for m in ["EER","FAR","FRR","Accuracy"]:
            results["SVM"][m].append(np.mean(svm_fold[m]))
            results["RandomForest"][m].append(np.mean(rf_fold[m]))

        print(f"[INFO]   SVM → EER: {np.mean(svm_fold['EER'])*100:.2f}%  "
              f"Acc: {np.mean(svm_fold['Accuracy'])*100:.2f}%")
        print(f"[INFO]   RF  → EER: {np.mean(rf_fold['EER'])*100:.2f}%   "
              f"Acc: {np.mean(rf_fold['Accuracy'])*100:.2f}%")

    # Итог
    print("\n" + "=" * 55)
    print("ИТОГ (mean ± std)")
    print("=" * 55)

    rows = []
    for name, metrics in results.items():
        row = {"Model": name}
        print(f"\n{name}:")
        for m, vals in metrics.items():
            mn = np.mean(vals) * 100
            st = np.std(vals)  * 100
            print(f"  {m:10s}: {mn:.2f}% ± {st:.2f}%")
            row[f"{m}_mean"] = round(np.mean(vals), 4)
            row[f"{m}_std"]  = round(np.std(vals),  4)
        rows.append(row)

    pd.DataFrame(rows).to_csv("hmog_baseline_results.csv", index=False)
    print("\n[INFO] Сохранено: hmog_baseline_results.csv")

    # DET кривая
    plt.figure(figsize=(7, 5))
    colors = {"SVM": ("royalblue", last_svm_res),
              "RF":  ("darkorange", last_rf_res)}
    for label, (color, res) in colors.items():
        if res:
            plt.plot(res["far"]*100, res["frr"]*100,
                     label=label, color=color, linewidth=2)
    plt.plot([0,100],[0,100],"k--",linewidth=1,label="EER Line")
    plt.xlabel("FAR (%)", fontsize=12)
    plt.ylabel("FRR (%)", fontsize=12)
    plt.title("DET Curve: SVM vs Random Forest\n(HMOG Dataset)", fontsize=12)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("hmog_det_curve_baseline.png", dpi=150)
    print("[INFO] График: hmog_det_curve_baseline.png")
    plt.show()

    # LaTeX
    print("\n--- LaTeX таблица (baseline) ---")
    print(r"\begin{tabular}{lcccc}")
    print(r"\hline")
    print(r"\textbf{Model} & \textbf{EER(\%)} & \textbf{FAR(\%)} "
          r"& \textbf{FRR(\%)} & \textbf{Acc(\%)} \\")
    print(r"\hline")
    for row in rows:
        n   = row["Model"]
        eer = f"{row['EER_mean']*100:.2f}±{row['EER_std']*100:.2f}"
        far = f"{row['FAR_mean']*100:.2f}±{row['FAR_std']*100:.2f}"
        frr = f"{row['FRR_mean']*100:.2f}±{row['FRR_std']*100:.2f}"
        acc = f"{row['Accuracy_mean']*100:.2f}±{row['Accuracy_std']*100:.2f}"
        print(f"{n} & {eer} & {far} & {frr} & {acc} \\\\")
    print(r"LSTM-only  & TBD & TBD & TBD & TBD \\")
    print(r"LSTM+Agent & TBD & TBD & TBD & TBD \\")
    print(r"\hline")
    print(r"\end{tabular}")

    print("\n[ГОТОВО] Теперь запустите hmog_lstm_light.py")