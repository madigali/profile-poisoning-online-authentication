# Paper 3 Evidence Hierarchy

This table records the inferential role of each experimental stage. It prevents exploratory HMOG development, branch-specific validation, diagnostics, and transferred external replication from being described as if they had the same confirmatory status.

| Stage | Dataset | Purpose | Parameter status | Data status | Inferential status | Outer test accessed? | Role in final claim |
|---|---|---|---|---|---|---|---|
| Paper 2 inherited baseline | HMOG | Define the accepted-only Blind EMA pipeline and unresolved update pathway | Inherited fixed implementation | Previously generated Paper 2 results and Paper 3 frozen score caches | Inherited context/baseline | Previously evaluated | Establishes the baseline mechanism; not a Paper 3 poisoning result |
| HMOG Attack v2 | HMOG | Test whether accepted impostor observations change future held-out ASR | Fixed folds, seeds, nested budgets, and poison/probe protocol | Outer HMOG scores accessed | Exploratory primary mechanism evidence | Yes | Main evidence for malicious inclusion |
| HMOG Guarded lambda sweep | HMOG | Intervene on update authorization and measure ASR/MUR/GUR trade-off | \(\lambda\in\{0,.25,.50,.75,1\}\) exploratory sweep; \(\lambda=.25\) carried forward | Same outer HMOG attack paths accessed | Exploratory; not untouched parameter confirmation | Yes | Security-control evidence and lambda-zero sanity check |
| HMOG clean-drift experiment | HMOG | Compare Frozen, Blind, and Guarded under controlled score-generating shifts | Frozen (D=0,1,2) synthetic sensitivity protocol | Outer HMOG drift scores accessed | Exploratory mechanism analysis | Yes | Tests accepted-only adaptation utility |
| Oracle-all diagnostic | HMOG | Change genuine update eligibility while holding EMA state equations fixed | Label-aware fixed diagnostic | Same outer clean-drift streams accessed | Diagnostic information-availability intervention | Yes | Evidence that feedback eligibility changes trajectory; not deployable or formally optimal |
| TQ-EMA v1 | HMOG | Test an isolated rejected-sample recovery route | Fold-specific validation selection and prespecified branch criterion | Validation and permitted outer test accessed | Branch-specific outer evaluation | Yes | Supporting negative recovery evidence |
| TQ-EMA v2 | HMOG | Test recovery-episode balancing | Frozen validation grid and fail-closed rule | Validation only; `outer_test_loaded=false` | Validation-stopped | No | No outer estimate; supporting stopped-branch evidence |
| Adaptive Quantile Profile | HMOG | Test a different score-state representation | Frozen \(\rho\) grid and fail-closed rule | Validation only; `outer_test_loaded=false` | Validation-stopped | No | No outer estimate; supporting stopped-branch evidence |
| McGill transferred replication | McGill | Test whether main poisoning, update-authorization, and feedback directions recur under a different dataset and real cross-day shift | Guarded \(\lambda=.25\), budgets, repeat count, and equations transferred; dataset-specific model fixed before Day 2 | Day 2 accessed only after viability gate | Independent directional mechanism-level replication; small-sample external evidence | Yes | External corroboration, not benchmark validation or broad effect-size generalization |
| Operating-point sensitivity | HMOG and McGill | Test whether reference poisoning and Guarded directions persist at nominal-5% and nominal-1% calibration-FAR conditions | Fixed score caches, \(\alpha\), \(\lambda\), pool semantics, seeds, calibration rules, and operating-point-specific \(k\)/boundary selection | Previously inspected HMOG test and McGill Day-2 caches reused | Prospectively specified sensitivity analysis; not untouched confirmation or external preregistration | Yes, previously evaluated caches | Defines operating-point scope, feasibility, gate activity, and strict-condition FRR cost |

## Paper-level reporting contrasts

- Historical primary security reporting contrast: HMOG reference boundary \(K=8\), Blind EMA minus Frozen post-poison ASR.
- Primary operating-point sensitivity contrast: HMOG nominal-1% boundary \(K=8\), Blind EMA minus Frozen post-poison ASR. It does not retroactively replace or confirm the historical contrast.
- Primary adaptation reporting contrast: HMOG claimant-only (D=2), Guarded versus Frozen late FRR, reported equivalently as Frozen-minus-Guarded late-FRR gain.
- TQ-EMA v1 retains its separately frozen branch-specific primary late-FRR endpoint.
- Other attack budgets, random attacks, lambda values, drift levels, and method contrasts are secondary or exploratory.

These labels define the final reporting focus. Reference and sensitivity rows use their own authoritative confidence intervals and cohort definitions. The labels do not retroactively make the sequential HMOG development or reused-cache sensitivity stage an untouched confirmatory study, and no post-hoc multiplicity correction was introduced.
