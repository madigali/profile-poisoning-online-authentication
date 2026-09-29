import os
import math
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

CACHE_DIR   = "cache_probas"
DRIFT_SWEEP = [0.0, 1.5, 2.5, 3.5]
N_FOLDS     = 5

AGENT_ALPHA_EMA  = 0.05
AGENT_K          = 1.5
AGENT_TAU0       = 0.3
AGENT_DECAY_RATE = 0.05
FLOOR_SWEEP      = [0.0, 0.1, 0.2, 0.3]

CASE_D_LEVELS   = [2.5, 3.5]   # магнитуды, на которых вердикт
CASE_RESID_MEAN = 10.0         # п.п., порог среднего остатка
CASE_FOLDS_MIN  = 4            # из 5 фолдов с остатком > 0
CASE_FAR_MAX    = 1.0          # %, правило выбора f*

CASE_HEADLINES = {
    1: "CASE 1 (constrained adaptation): агент с f* бьёт ЛЮБУЮ "
       "фиксированную калибровку при matched OP (включая FRR-якорь). "
       "Floor — часть метода; хедлайн: адаптация сохраняет рабочую "
       "точку под дрейфом только при ограничении безопасности.",
    2: "CASE 2 (automation): выигрыш только по FAR-якорю; по FRR-якорю "
       "остаток ~0. Хедлайн: агент автоматически находит безопасную "
       "drift-устойчивую OP; ценности в автоматизации перекалибровки, "
       "а не в робастности поверх выбора точки.",
    3: "CASE 3 (pure variant A): адаптация не даёт ничего поверх "
       "рабочей точки ни при каком floor. Хедлайн: диагностический "
       "negative result + дизайн-урок (floor/аттрактор).",
}

class AdaptiveAgentEMA:
    def __init__(self, alpha=AGENT_ALPHA_EMA, k=AGENT_K,
                 init_threshold=AGENT_TAU0,
                 decay_rate=AGENT_DECAY_RATE, floor=0.0):
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

def run_agent(scores, order_idx, floor=0.0):
    agent = AdaptiveAgentEMA(floor=floor)
    decisions = np.zeros(len(scores), dtype=bool)
    margins   = np.zeros(len(scores), dtype=np.float64)
    for idx in order_idx:
        is_g, m = agent.decide(float(scores[idx]))
        decisions[idx] = is_g
        margins[idx]   = m
    return decisions, margins

def compute_eer(genuine, impostor):
    all_s = np.concatenate([genuine, impostor])
    thrs  = np.percentile(all_s, np.linspace(0, 100, 500))
    far = np.array([np.sum(impostor >= t) / max(len(impostor), 1)
                    for t in thrs])
    frr = np.array([np.sum(genuine  <  t) / max(len(genuine),  1)
                    for t in thrs])
    i = np.argmin(np.abs(far - frr))
    return (far[i] + frr[i]) / 2.0, thrs[i]

def load_cache(fold, D):
    path = os.path.join(CACHE_DIR, f"fold{fold}_D{D}.npz")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Нет кеша: {path}. Сначала python hmog_cache_probas.py")
    z = np.load(path)
    return z["probas"], z["yte"], z["te_groups"], z["drift_frac"]

def static_op_curve(g_early, i_early, g_late, i_late, n_points=200):
    all_e = np.concatenate([g_early, i_early])
    thrs  = np.percentile(all_e, np.linspace(0, 100, n_points))
    far_e = np.array([np.mean(i_early >= t) for t in thrs])
    frr_e = np.array([np.mean(g_early <  t) for t in thrs])
    frr_l = np.array([np.mean(g_late  <  t) for t in thrs])
    far_l = np.array([np.mean(i_late  >= t) for t in thrs])
    return far_e, frr_e, frr_l - frr_e, far_l

def interp_at(x_curve, y_curve, x_target):
    o = np.argsort(x_curve)
    xs, ys = x_curve[o], y_curve[o]
    if x_target <= xs[0]:
        return float(ys[0])
    if x_target >= xs[-1]:
        return float(ys[-1])
    return float(np.interp(x_target, xs, ys))

def run_matched_op_by_floor():
    print("\n" + "=" * 66)
    print("[E1] MATCHED-OP PER FLOOR (оба якоря, per-fold остатки)")
    print("=" * 66)
    rows = []
    for floor in FLOOR_SWEEP:
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
                    if len(g_e) < 2 or len(i_e) < 2 or \
                       len(g_l) < 1 or len(i_l) < 1:
                        continue
                    dec, _ = run_agent(scores, order, floor=floor)
                    a_far_e = float(np.mean(dec[early_mask & (true_bin == 0)]))
                    a_frr_e = float(np.mean(~dec[early_mask & (true_bin == 1)]))
                    a_frr_l = float(np.mean(~dec[late_mask  & (true_bin == 1)]))
                    a_far_l = float(np.mean(dec[late_mask   & (true_bin == 0)]))
                    far_e, frr_e, dfrr_s, far_l = static_op_curve(
                        g_e, i_e, g_l, i_l)
                    per_subj.append({
                        "agent_FAR_early": a_far_e,
                        "agent_FRR_early": a_frr_e,
                        "agent_FAR_late":  a_far_l,
                        "agent_FRR_late":  a_frr_l,
                        "dFRR_agent":      a_frr_l - a_frr_e,
                        "dFRR_static_mFAR": interp_at(far_e, dfrr_s, a_far_e),
                        "dFRR_static_mFRR": interp_at(frr_e, dfrr_s, a_frr_e),
                        "FAR_late_static_mFAR": interp_at(far_e, far_l, a_far_e),
                    })
                if not per_subj:
                    continue
                m = pd.DataFrame(per_subj).mean() * 100   # per-subject -> mean
                rows.append({"floor": floor, "fold": fold, "D": D,
                             **m.to_dict()})
        print(f"  [floor={floor:.1f}] готово")
    df = pd.DataFrame(rows)
    df.to_csv("analysis_E_matched_op_by_floor.csv", index=False)
    return df

def print_floor_summary(df):
    print("\n  --- СВОДКА ПО FLOOR (среднее по фолдам; folds>0 = число "
          "фолдов с остатком > 0) ---")
    for floor in FLOOR_SWEEP:
        print(f"\n  floor={floor:.1f}")
        print("    D  | dFRR_ag | st@mFAR | st@mFRR | res_mFAR (f>0) "
              "| res_mFRR (f>0) | FAR_l_ag")
        for D in DRIFT_SWEEP:
            s = df[(df["floor"] == floor) & (df["D"] == D)]
            if s.empty:
                continue
            r_far = s["dFRR_static_mFAR"] - s["dFRR_agent"]
            r_frr = s["dFRR_static_mFRR"] - s["dFRR_agent"]
            print(f"   {D:>4.1f} | {s['dFRR_agent'].mean():+7.2f} | "
                  f"{s['dFRR_static_mFAR'].mean():+7.2f} | "
                  f"{s['dFRR_static_mFRR'].mean():+7.2f} | "
                  f"{r_far.mean():+7.2f} ({int((r_far > 0).sum())}/5) | "
                  f"{r_frr.mean():+7.2f} ({int((r_frr > 0).sum())}/5) | "
                  f"{s['agent_FAR_late'].mean():6.2f}%")

def run_ablation_by_floor():
    print("\n" + "=" * 66)
    print("[E2] ABLATION PER FLOOR при D=0 (margin-EER)")
    print("=" * 66)
    rows = []
    for floor in FLOOR_SWEEP:
        fold_rows = []
        for fold in range(1, N_FOLDS + 1):
            probas, yte, te_groups, drift_frac = load_cache(fold, 0.0)
            order = np.argsort(drift_frac, kind="stable")
            eer_l, eer_a = [], []
            for sid in np.unique(yte):
                scores   = probas[:, sid]
                true_bin = (yte == sid).astype(int)
                g, i = scores[true_bin == 1], scores[true_bin == 0]
                if len(g) < 2 or len(i) < 2:
                    continue
                e1, _ = compute_eer(g, i)
                eer_l.append(e1)
                _, margins = run_agent(scores, order, floor=floor)
                gm, im = margins[true_bin == 1], margins[true_bin == 0]
                e2, _ = compute_eer(gm, im)
                eer_a.append(e2)
            fold_rows.append({"fold": fold,
                              "EER_lstm_only": np.mean(eer_l) * 100,
                              "EER_agent":     np.mean(eer_a) * 100})
        d = pd.DataFrame(fold_rows)
        rows.append({"floor": floor,
                     "EER_lstm_mean": d["EER_lstm_only"].mean(),
                     "EER_lstm_std":  d["EER_lstm_only"].std(),
                     "EER_agent_mean": d["EER_agent"].mean(),
                     "EER_agent_std":  d["EER_agent"].std()})
        print(f"  floor={floor:.1f}: LSTM-only {rows[-1]['EER_lstm_mean']:.2f}"
              f"±{rows[-1]['EER_lstm_std']:.2f}%  |  +Agent "
              f"{rows[-1]['EER_agent_mean']:.2f}±{rows[-1]['EER_agent_std']:.2f}%")
    df = pd.DataFrame(rows)
    df.to_csv("analysis_E_ablation_by_floor.csv", index=False)
    return df

def decide_case(df):
    print("\n" + "=" * 66)
    print("[E3] ВЕРДИКТ КЕЙСА")
    print("=" * 66)
    # f*: минимальный floor с max_D FAR_late <= CASE_FAR_MAX
    fstar = None
    for floor in FLOOR_SWEEP:
        s = df[df["floor"] == floor]
        max_far = s.groupby("D")["agent_FAR_late"].mean().max()
        if max_far <= CASE_FAR_MAX:
            fstar = floor
            break
    if fstar is None:
        fstar = FLOOR_SWEEP[-1]
    print(f"  f* = {fstar:.1f}  (правило: мин. floor с max_D "
          f"FAR_late <= {CASE_FAR_MAX}%)")

    s = df[df["floor"] == fstar]
    table = []
    for D in CASE_D_LEVELS:
        sd = s[s["D"] == D]
        r_far = (sd["dFRR_static_mFAR"] - sd["dFRR_agent"]).to_numpy()
        r_frr = (sd["dFRR_static_mFRR"] - sd["dFRR_agent"]).to_numpy()
        table.append({"D": D,
                      "mean_mFAR": float(r_far.mean()),
                      "npos_mFAR": int((r_far > 0).sum()),
                      "mean_mFRR": float(r_frr.mean()),
                      "npos_mFRR": int((r_frr > 0).sum())})
        print(f"  D={D:>4.1f}: resid(mFAR)={r_far.mean():+7.2f} п.п. "
              f"({int((r_far > 0).sum())}/5 > 0) | "
              f"resid(mFRR)={r_frr.mean():+7.2f} п.п. "
              f"({int((r_frr > 0).sum())}/5 > 0)")

    case1 = all(t["mean_mFRR"] >= CASE_RESID_MEAN and
                t["npos_mFRR"] >= CASE_FOLDS_MIN for t in table)
    case2 = (not case1) and all(t["mean_mFAR"] >= CASE_RESID_MEAN and
                                t["npos_mFAR"] >= CASE_FOLDS_MIN for t in table)
    case = 1 if case1 else (2 if case2 else 3)
    print(f"\n  ==> CASE {case}")
    print(f"  {CASE_HEADLINES[case]}")
    return case, fstar, pd.DataFrame(table)

if __name__ == "__main__":
    print("=" * 66)
    print("ФИНАЛЬНЫЙ КОНТРОЛЬ [E]: matched-OP per floor + вердикт")
    print("=" * 66)
    if not os.path.isdir(CACHE_DIR):
        print(f"[ERROR] Нет {CACHE_DIR}/. Запустите hmog_cache_probas.py")
        exit(1)
    df_e  = run_matched_op_by_floor()
    print_floor_summary(df_e)
    df_ab = run_ablation_by_floor()
    case, fstar, tab = decide_case(df_e)
    print("\n  --- ЧТО БЕРЁМ В СТАТЬЮ ---")
    print(f"  конфигурация метода: floor={fstar:.1f}")
    row = df_ab[df_ab["floor"] == fstar].iloc[0]
    print(f"  строка Table 4 (LSTM+Agent): EER {row['EER_agent_mean']:.2f}"
          f"±{row['EER_agent_std']:.2f}%  (LSTM-only "
          f"{row['EER_lstm_mean']:.2f}±{row['EER_lstm_std']:.2f}%)")
    print("  Новые экспериментальные ветки ЗАКРЫТЫ независимо от кейса.")