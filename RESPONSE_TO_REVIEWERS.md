# Response to reviewers

We thank all three reviewers for identifying weaknesses in the original
submission. We performed a complete code and manuscript audit rather than only
editing the presentation. During that audit we found an additional critical
data-parsing defect: the earlier pipeline read HMOG metadata columns as sensor
axes, allowing a subject/session identifier to enter the feature vector. We
therefore withdraw every numerical result from the original submission and
report only the newly executed, leakage-resistant experiment. The revised
manuscript makes this correction explicit and no longer claims superiority from
the invalid earlier numbers.

## Reviewer 1

### Novelty relative to the extensive continuous-authentication literature

We agree that continuous authentication, HMOG, LSTM classification, and EMA are
individually established ideas. The revised Related Work cites the two surveys
suggested by the reviewer (Gonzalez-Manzano et al.; Ayeswarya and Norman), adds a
positioning table, and narrows the contribution. We now claim a controlled,
session-disjoint evaluation of an online EMA operating point, including a
same-classifier ablation and causal drift test. We removed statements that the
general combination is unprecedented or that it outperforms incomparable prior
work.

### Evaluation on more datasets

We agree that a second dataset is necessary for strong external-validity
claims. No additional suitable dataset is present in the project, and we did not
fabricate or substitute evidence. The revised paper now states this as a central
limitation and confines its conclusions to HMOG. Repeating the locked protocol
on a second session-rich inertial corpus is the first required extension.

### Need for a proposal overview

The revised Method begins with a five-stage system overview: sensor samples,
non-overlapping windows, statistical features, LSTM score, and static or EMA
decision. It also identifies which stages are shared by the ablation, making the
agent's role explicit.

### Justification of alpha and K

The revised agent has no sliding score buffer and therefore no unexplained
`K=10`. Each claimant's `k` is induced by the validation EER threshold:
`k=(p_0-tau_0)/sigma_0`, so the initial adaptive and frozen operating points are
identical. We fix `alpha=0.05`, which gives an effective EMA memory of
approximately 20 accepted attempts. Neither quantity is selected from test
performance.

## Reviewer 2

### Missing LSTM-only ablation

Added. The frozen and adaptive variants use the same trained LSTM, the same
scores, and exactly the same enrollment-derived initial threshold. The only
difference is whether accepted scores update the first two EMA moments. The
revised paper reports FAR, FRR, and HTER for the actual causal decisions of both
variants. The result is negative: clean HTER is $23.19\%\pm0.95\%$ for the
frozen threshold and $24.53\%\pm1.28\%$ for the EMA agent.

### EMA profile absent from the decision equation

Corrected in both code and manuscript. The revised threshold is

`tau_n = max(0, p_(n-1) - k * sqrt(q_(n-1) - p_(n-1)^2))`,

and the decision is `score_n >= tau_n`. Accepted scores update both `p` and `q`;
rejections leave the state unchanged. The earlier, disconnected sliding-mean
equation and fixed `tau=0.5` have been removed.

### Drift was asserted but not demonstrated

Added. The identical fitted model is evaluated at standardized feature-space
drift magnitudes 0, 1, and 2. Frozen and EMA thresholds are compared under the
same score stream. Synthetic drift is explicitly labeled as a controlled
covariate-shift test, not as proof of every natural behavioral change. At
$\lVert\delta\rVert_2=2$, HTER is $24.89\%\pm1.37\%$ (frozen) versus
$26.39\%\pm2.12\%$ (EMA); the adaptive claim is therefore withdrawn.

### Overlapping sequences across folds

Corrected more strongly than requested. Raw one-second windows do not overlap;
10-window evaluation sequences also do not overlap. Sequences are constructed
inside one session only, and entire sessions are assigned to fit, validation,
or test. No raw window or sequence can straddle a partition boundary.

### Z-score leakage

Corrected and documented. The scaler is fitted only on the model-fitting
sessions, then applied unchanged to validation and test. Validation sessions are
also excluded from the training loader.

### Training paragraph, notation, and parameters

The training description now appears immediately after the LSTM architecture.
Sequence time and online attempt indices are distinct. The hyperparameters and
formulas match the canonical implementation.

## Reviewer 3

The revised work addresses the reviewer's concerns through the same substantive
changes: corrected feature parsing, disjoint fit/validation/test sessions,
training-only normalization, enrollment-only threshold initialization, a causal
EMA decision, an LSTM-only ablation, and a controlled drift experiment. Test
EER is now described only as a separability statistic. Deployable FAR/FRR/HTER
are computed at thresholds that never use test labels. We also removed the
class-imbalance-sensitive one-vs-all accuracy headline.

## Additional corrections found during the audit

- The older agent lowered its threshold after every rejection, eventually
  producing fail-open behavior and allowing accepted impostors to poison the
  profile. Rejections no longer lower the threshold.
- The former `GroupKFold` did not include all 100 subjects in every test fold.
  The new deterministic session rule requires every included subject in every
  fit, validation, and test partition.
- Earlier SVM/RF baselines used one-second windows while the LSTM used longer
  sequences. All classifiers now receive the same 10-second endpoint.
- The old baseline DET plot represented only the final subject in the final
  fold and has been removed from the revised manuscript.
- All legacy CSV and figures are excluded from the revised evidence. The new
  experiment records fold assignments, quality exclusions, configuration, and
  per-fold results in `revised_results/`.
