# ============================================================
# hmog_analysis.py  —  ДЕШЁВЫЙ АНАЛИЗ ИЗ КЕША
#
# Читает ./cache_probas/*.npz (созданные hmog_cache_probas.py)
# и считает, БЕЗ переобучения:
#
#   [A] ABLATION при D=0: LSTM-only vs LSTM+AdaptiveAgentEMA
#       (вариант 1: агент статьи = AdaptiveAgentEMA)
#   [B] OP-КРИВАЯ: сетка статических порогов на early ->
#       (FAR_early, FRR_early, dFRR, FAR_late)
#   [C] MATCHED-OP: интерполяция OP-кривой в точке агента
#       (по FAR_early и отдельно по FRR_early). РЕШАЮЩИЙ КОНТРОЛЬ:
#       остаток = dFRR_static_matched - dFRR_agent
#   [D] FLOOR-SENSITIVITY: агент с floor in {0.0,0.1,0.2,0.3}
#
# Все результаты -> CSV + печать. Перезапускается за секунды.
# ============================================================

import os
import math
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

CACHE_DIR   = "cache_probas"
DRIFT_SWEEP = [0.0, 1.5, 2.5, 3.5]
N_FOLDS     = 5

# --- Гиперпараметры агента (как в hmog_lstm_light.py v4) ---
AGENT_ALPHA_EMA  = 0.05
AGENT_K          = 1.5
AGENT_TAU0       = 0.3
AGENT_DECAY_RATE = 0.05
AGENT_FLOOR      = 0.0

FLOOR_SWEEP = [0.0, 0.1, 0.2, 0.3]

# ============================================================
# Агент (точная копия из hmog_lstm_light.py v4)
# ============================================================

class AdaptiveAgentEMA:
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


def run_agent(scores, order_idx, floor=AGENT_FLOOR):
    agent = AdaptiveAgentEMA(floor=floor)
    decisions = np.zeros(len(scores), dtype=bool)
    margins   = np.zeros(len(scores), dtype=np.float64)
    for idx in order_idx:
        is_g, m = agent.decide(float(scores[idx]))
        decisions[idx] = is_g
        margins[idx]   = m
    return decisions, margins

# ============================================================
# Метрики
# ============================================================

def compute_eer(genuine, impostor):
    all_s = np.concatenate([genuine, impostor])
    thrs  = np.percentile(all_s, np.linspace(0, 100, 500))
    far = np.array([np.sum(impostor >= t) / max(len(impostor), 1) for t in thrs])
    frr = np.array([np.sum(genuine  <  t) / max(len(genuine),  1) for t in thrs])
    i = np.argmin(np.abs(far - frr))
    return (far[i] + frr[i]) / 2.0, thrs[i]

# ============================================================
# Загрузка кеша
# ============================================================

def load_cache(fold, D):
    path = os.path.join(CACHE_DIR, f"fold{fold}_D{D}.npz")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Нет кеша: {path}. Сначала запустите hmog_cache_probas.py")
    z = np.load(path)
    return z["probas"], z["yte"], z["te_groups"], z["drift_frac"]

# ============================================================
# [A] ABLATION при D=0
# ============================================================

def run_ablation():
    print("\n" + "=" * 60)
    print("[A] ABLATION при D=0: LSTM-only vs LSTM+AdaptiveAgentEMA")
    print("=" * 60)

    rows = []
    for fold in range(1, N_FOLDS + 1):
        probas, yte, te_groups, drift_frac = load_cache(fold, 0.0)
        order = np.argsort(drift_frac, kind="stable")

        eer_lstm, eer_agent = [], []
        for sid in np.unique(yte):
            scores   = probas[:, sid]
            true_bin = (yte == sid).astype(int)
            g, i = scores[true_bin == 1], scores[true_bin == 0]
            if len(g) < 2 or len(i) < 2:
                continue
            e1, _ = compute_eer(g, i)
            eer_lstm.append(e1)

            _, margins = run_agent(scores, order)
            gm, im = margins[true_bin == 1], margins[true_bin == 0]
            e2, _ = compute_eer(gm, im)
            eer_agent.append(e2)

        rows.append({"fold": fold,
                     "EER_lstm_only": np.mean(eer_lstm) * 100,
                     "EER_agent":     np.mean(eer_agent) * 100})
        print(f"  fold{fold}: LSTM-only={rows[-1]['EER_lstm_only']:.2f}%  "
              f"Agent={rows[-1]['EER_agent']:.2f}%")

    df = pd.DataFrame(rows)
    print(f"\n  ИТОГ: LSTM-only  {df.EER_lstm_only.mean():.2f}% "
          f"± {df.EER_lstm_only.std():.2f}%")
    print(f"        LSTM+Agent {df.EER_agent.mean():.2f}% "
          f"± {df.EER_agent.std():.2f}%")
    df.to_csv("analysis_A_ablation.csv", index=False)
    return df

# ============================================================
# [B]+[C] OP-КРИВАЯ и MATCHED-OP
# ============================================================

def static_op_curve(g_early, i_early, g_late, i_late, n_points=200):
    """Возвращает массивы (FAR_e, FRR_e, dFRR, FAR_l) по сетке порогов."""
    all_e = np.concatenate([g_early, i_early])
    thrs  = np.percentile(all_e, np.linspace(0, 100, n_points))
    far_e = np.array([np.mean(i_early >= t) for t in thrs])
    frr_e = np.array([np.mean(g_early <  t) for t in thrs])
    frr_l = np.array([np.mean(g_late  <  t) for t in thrs])
    far_l = np.array([np.mean(i_late  >= t) for t in thrs])
    return far_e, frr_e, frr_l - frr_e, far_l


def interp_at(x_curve, y_curve, x_target):
    """Интерполяция y в точке x_target (x_curve может быть не монотонна ->
    сортируем)."""
    o = np.argsort(x_curve)
    xs, ys = x_curve[o], y_curve[o]
    if x_target <= xs[0]:
        return ys[0]
    if x_target >= xs[-1]:
        return ys[-1]
    return float(np.interp(x_target, xs, ys))


def run_matched_op():
    print("\n" + "=" * 60)
    print("[B]+[C] OP-КРИВАЯ и MATCHED-OP (решающий контроль)")
    print("=" * 60)

    rows = []
    for fold in range(1, N_FOLDS + 1):
        for D in DRIFT_SWEEP:
            probas, yte, te_groups, drift_frac = load_cache(fold, D)
            order      = np.argsort(drift_frac, kind="stable")
            early_mask = drift_frac < 0.5
            late_mask  = ~early_mask

            per_subj = []
            for sid in np.unique(yte):
                scores   = probas[:, sid]
                true_bin = (yte == sid).astype(int)

                g_e = scores[early_mask & (true_bin == 1)]
                i_e = scores[early_mask & (true_bin == 0)]
                g_l = scores[late_mask  & (true_bin == 1)]
                i_l = scores[late_mask  & (true_bin == 0)]
                if len(g_e) < 2 or len(i_e) < 2 or len(g_l) < 1 or len(i_l) < 1:
                    continue

                # --- агент: его фактическая рабочая точка ---
                dec, _ = run_agent(scores, order)
                agent_far_e = np.mean(dec[early_mask & (true_bin == 0)])
                agent_frr_e = np.mean(~dec[early_mask & (true_bin == 1)])
                agent_frr_l = np.mean(~dec[late_mask  & (true_bin == 1)])
                agent_far_l = np.mean(dec[late_mask   & (true_bin == 0)])
                dfrr_agent  = agent_frr_l - agent_frr_e

                # --- статическая OP-кривая ---
                far_e, frr_e, dfrr_s, far_l = static_op_curve(
                    g_e, i_e, g_l, i_l)

                # matched по FAR_early
                dfrr_matched_far = interp_at(far_e, dfrr_s, agent_far_e)
                far_l_matched    = interp_at(far_e, far_l,  agent_far_e)
                # matched по FRR_early
                dfrr_matched_frr = interp_at(frr_e, dfrr_s, agent_frr_e)

                # EER-точка static (то, что было в v4)
                _, thr_eer = compute_eer(g_e, i_e)
                dfrr_static_eer = np.mean(g_l < thr_eer) - np.mean(g_e < thr_eer)

                per_subj.append({
                    "agent_FAR_early": agent_far_e,
                    "agent_FRR_early": agent_frr_e,
                    "agent_FAR_late":  agent_far_l,
                    "dFRR_agent":      dfrr_agent,
                    "dFRR_static_EER":         dfrr_static_eer,
                    "dFRR_static_matchedFAR":  dfrr_matched_far,
                    "dFRR_static_matchedFRR":  dfrr_matched_frr,
                    "FAR_late_static_matched": far_l_matched,
                })

            if not per_subj:
                continue
            m = pd.DataFrame(per_subj).mean() * 100
            rows.append({"fold": fold, "D": D, **m.to_dict()})
            print(f"  fold{fold} D={D:>4.1f} | "
                  f"dFRR agent={m['dFRR_agent']:+6.2f} | "
                  f"static@EER={m['dFRR_static_EER']:+6.2f} | "
                  f"static@matchedFAR={m['dFRR_static_matchedFAR']:+6.2f} | "
                  f"agent FAR_e={m['agent_FAR_early']:.1f}%")

    df = pd.DataFrame(rows)
    df.to_csv("analysis_BC_matched_op.csv", index=False)

    print("\n  --- ДЕКОМПОЗИЦИЯ (среднее по фолдам) ---")
    print("  D    dFRR_agent  static@EER  static@mFAR  static@mFRR  "
          "ОСТАТОК(mFAR)")
    for D in DRIFT_SWEEP:
        s = df[df.D == D]
        if s.empty:
            continue
        resid = s.dFRR_static_matchedFAR.mean() - s.dFRR_agent.mean()
        print(f"  {D:>4.1f} {s.dFRR_agent.mean():>10.2f} "
              f"{s.dFRR_static_EER.mean():>11.2f} "
              f"{s.dFRR_static_matchedFAR.mean():>12.2f} "
              f"{s.dFRR_static_matchedFRR.mean():>12.2f} "
              f"{resid:>14.2f}")

    print("\n  ПРАВИЛО ИНТЕРПРЕТАЦИИ:")
    print("   остаток <= 5 п.п.  -> адаптационный эффект ~0 (variant A)")
    print("   остаток >= 10 п.п. -> адаптация даёт выигрыш поверх")
    print("                         выбора рабочей точки")
    return df

# ============================================================
# [D] FLOOR-SENSITIVITY
# ============================================================

def run_floor_sweep():
    print("\n" + "=" * 60)
    print("[D] FLOOR-SENSITIVITY: можно ли увести агента из FAR~40%")
    print("=" * 60)

    rows = []
    for floor in FLOOR_SWEEP:
        for D in DRIFT_SWEEP:
            fold_far, fold_dfrr = [], []
            for fold in range(1, N_FOLDS + 1):
                probas, yte, te_groups, drift_frac = load_cache(fold, D)
                order      = np.argsort(drift_frac, kind="stable")
                early_mask = drift_frac < 0.5
                late_mask  = ~early_mask

                fars, dfrrs = [], []
                for sid in np.unique(yte):
                    scores   = probas[:, sid]
                    true_bin = (yte == sid).astype(int)
                    if (early_mask & (true_bin == 1)).sum() < 1 or \
                       (late_mask  & (true_bin == 1)).sum() < 1:
                        continue
                    dec, _ = run_agent(scores, order, floor=floor)
                    frr_e = np.mean(~dec[early_mask & (true_bin == 1)])
                    frr_l = np.mean(~dec[late_mask  & (true_bin == 1)])
                    far_l = np.mean(dec[late_mask   & (true_bin == 0)])
                    fars.append(far_l)
                    dfrrs.append(frr_l - frr_e)
                if fars:
                    fold_far.append(np.mean(fars))
                    fold_dfrr.append(np.mean(dfrrs))

            rows.append({"floor": floor, "D": D,
                         "agent_FAR_late": np.mean(fold_far) * 100,
                         "dFRR_agent":     np.mean(fold_dfrr) * 100})
            print(f"  floor={floor:.1f} D={D:>4.1f} | "
                  f"FAR_late={rows[-1]['agent_FAR_late']:5.1f}% | "
                  f"dFRR={rows[-1]['dFRR_agent']:+6.2f} п.п.")

    df = pd.DataFrame(rows)
    df.to_csv("analysis_D_floor_sweep.csv", index=False)
    return df

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("АНАЛИЗ ИЗ КЕША (без переобучения)")
    print("=" * 60)

    if not os.path.isdir(CACHE_DIR):
        print(f"[ERROR] Нет папки {CACHE_DIR}/. "
              f"Сначала запустите: python hmog_cache_probas.py")
        exit(1)

    df_a = run_ablation()
    df_bc = run_matched_op()
    df_d = run_floor_sweep()

    print("\n" + "=" * 60)
    print("ФАЙЛЫ: analysis_A_ablation.csv, analysis_BC_matched_op.csv, "
          "analysis_D_floor_sweep.csv")
    print("=" * 60)