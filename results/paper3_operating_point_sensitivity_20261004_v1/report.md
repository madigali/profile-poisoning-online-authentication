# Operating-point sensitivity report

Status: **complete**.

Reference reproduction: **PASS**.

The nominal targets are calibration constraints, not observed held-out FAR guarantees.

## Held-out Frozen operating points

| Dataset | Condition | Calibration FAR | Held-out FAR | FRR | HTER |
|---|---:|---:|---:|---:|---:|
| HMOG | reference | 23.01% | 22.92% | 24.95% | 23.94% |
| HMOG | far_5pct | 4.93% | 5.07% | 57.88% | 31.48% |
| HMOG | far_1pct | 0.91% | 1.04% | 80.79% | 40.91% |
| McGill | reference | 6.89% | 12.20% | 78.81% | 45.51% |
| McGill | far_5pct | 3.66% | 7.37% | 82.43% | 44.90% |
| McGill | far_1pct | 0.79% | 2.14% | 90.25% | 46.20% |

## Boundary K=8 effects

| Dataset | Condition | Eligible paths | Victims | Contrast | Effect [95% CI], pp |
|---|---:|---:|---:|---|---:|
| HMOG | reference | 49889 | 100 | Blind EMA minus Frozen | +31.04 [+26.97, +35.11] |
| HMOG | reference | 49889 | 100 | Guarded EMA minus Blind EMA | -31.02 [-35.15, -26.98] |
| HMOG | far_5pct | 49753 | 100 | Blind EMA minus Frozen | +2.49 [+0.95, +4.38] |
| HMOG | far_5pct | 49753 | 100 | Guarded EMA minus Blind EMA | -3.09 [-4.91, -1.61] |
| HMOG | far_1pct | 9088 | 100 | Blind EMA minus Frozen | -0.45 [-0.50, -0.39] |
| HMOG | far_1pct | 9088 | 100 | Guarded EMA minus Blind EMA | -0.01 [-0.02, -0.00] |
| McGill | reference | 1456 | 18 | Blind EMA minus Frozen | +19.72 [+5.50, +37.24] |
| McGill | reference | 1456 | 18 | Guarded EMA minus Blind EMA | -19.62 [-36.77, -5.66] |
| McGill | far_5pct | 1369 | 18 | Blind EMA minus Frozen | +0.20 [-0.05, +0.53] |
| McGill | far_5pct | 1369 | 18 | Guarded EMA minus Blind EMA | -0.26 [-0.58, -0.03] |
| McGill | far_1pct | 1001 | 17 | Blind EMA minus Frozen | -0.35 [-0.55, -0.19] |
| McGill | far_1pct | 1001 | 17 | Guarded EMA minus Blind EMA | +0.00 [+0.00, +0.00] |

## Interpretation guardrails

- Boundary estimates are conditional on operating-point-specific K=8 feasibility.
- Cross-target effects can involve different paths and must not be read as strictly paired target comparisons.
- The victim bootstrap conditions on fixed trained models and observed probe pools.
- The victim×source analysis is secondary and does not remove classifier-training or population uncertainty.

## Primary victim×source sensitivity

- Blind EMA minus Frozen: -0.45 pp, 95% CI [-0.52, -0.38] (complete_product_weight_victim_source_bootstrap).
- Guarded EMA minus Blind EMA: -0.01 pp, 95% CI [-0.02, -0.00] (complete_product_weight_victim_source_bootstrap).
- Guarded EMA minus Frozen: -0.46 pp, 95% CI [-0.52, -0.40] (complete_product_weight_victim_source_bootstrap).
