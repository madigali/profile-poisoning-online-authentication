# Supplementary Methods

## S1. Evidential Status of the Supporting Recovery Probes

The recovery and alternative-state branches used the frozen HMOG claimant-only \(D=2\) score protocol described in the main Methods. TQ-EMA v1 reached its permitted outer evaluation after fold-specific validation selection. TQ-EMA v2 and the Adaptive Quantile Profile used fail-closed validation rules: if any fold lacked a feasible configuration, outer test scores were not loaded. Moving their detailed specifications to the Supplement does not change their historical protocols, endpoints, or inferential status.

TQ-EMA v1 is therefore an outer-evaluated supporting probe, whereas TQ-EMA v2 and the Adaptive Quantile Profile are validation-only stopped branches. The latter two cannot support outer-performance claims. Their manifests record `outer_test_loaded=false`.

## S2. TQ-EMA v1 State and Transition Rules

TQ-EMA v1 added an isolated recovery path while retaining the Guarded trusted path at \(\lambda=0.25\). Production state contained the EMA mean, second moment, derived standard deviation, and derived authentication threshold. Quarantine state contained candidate scores, distinct session identifiers, a downward-shift direction, and age. Resetting quarantine did not alter production state.

The trusted path used the same conjunction as Guarded EMA. With

\[
\tau^{\mathrm{update,raw}}_t
=\tau^{\mathrm{auth}}_t+\lambda(\mu_0-\tau^{\mathrm{auth}}_t),
\]

an update was permitted only when the observation was authenticated and \(s_t\geq\tau^{\mathrm{update,raw}}_t\). Equivalently, the effective trusted threshold was

\[
\tau^{\mathrm{update,effective}}_t
=\max(\tau^{\mathrm{auth}}_t,\tau^{\mathrm{update,raw}}_t).
\]

The four observation paths were:

1. If \(s_t\geq\tau^{\mathrm{update,effective}}_t\), access was granted and a bounded canonical EMA proposal was considered.
2. If \(\tau^{\mathrm{auth}}_t\leq s_t<\tau^{\mathrm{update,effective}}_t\), access was granted but production state was not updated.
3. If \(\tau^{\mathrm{auth}}_t-b\leq s_t<\tau^{\mathrm{auth}}_t\), access was denied and the observation entered recovery quarantine only.
4. If \(s_t<\tau^{\mathrm{auth}}_t-b\), access was denied, the observation was discarded, and quarantine was reset.

Recovery required \(m\) consecutive candidates from distinct sessions. Every candidate had to be below the production mean recorded when the quarantine run began, and the batch range could not exceed \(r\). An intervening non-candidate reset the run. A confirmed batch used the median score as its robust target and proposed a small joint update of the first and second moments. Standard deviation and authentication threshold were recomputed from those moments; the threshold was not edited independently.

Trusted and recovery proposals had to satisfy

\[
|\Delta\mu|\leq c_\mu,
\qquad
|\Delta\tau|\leq c_\tau,
\qquad
\tau\geq\tau_{\mathrm{enroll}}-A.
\]

A recovery proposal that did not lower the derived threshold was rejected.

## S3. TQ-EMA v1 Validation and Selection

Dimensional controls were scaled by the fixed enrollment standard deviation. The validation grid was

\[
b/\sigma_{\mathrm{enroll}}\in\{0.25,0.50,0.75\},
\quad
m\in\{2,3\},
\]

\[
\alpha_{\mathrm{recovery}}\in\{0.025,0.050\},
\quad
A/\sigma_{\mathrm{enroll}}\in\{0.10,0.25\}.
\]

Fixed controls were \(r=0.50\sigma_{\mathrm{enroll}}\), \(c_\mu=0.10\sigma_{\mathrm{enroll}}\), \(c_\tau=0.05\sigma_{\mathrm{enroll}}\), trusted-path \(\lambda=0.25\), and trusted-path \(\alpha=0.05\).

Selection was nested within each outer fold and used validation data only. The first two complete chronological validation sessions initialized and calibrated the inner profile; the remaining sessions formed the tuning stream. Claimant validation observations used the independently generated \(D=2\) scores and impostor checkpoints used \(D=0\). Among configurations with subject-macro late-FAR change no greater than +1.0 percentage point relative to Frozen, the configuration with the largest late-FRR gain was selected, with conservative tie-breaking. The +1.0-point FAR limit was an experiment-specific constraint rather than a universal standard.

The primary endpoint was Frozen late FRR minus TQ-EMA late FRR. Success required (i) the lower bound of the paired 95% subject-bootstrap interval to exceed zero, (ii) mean late-FAR increase no greater than +1.0 point, (iii) mean HTER degradation no greater than +0.5 point, and (iv) the same conclusion in the 99-subject complete-five-fold cohort.

## S4. TQ-EMA v2 Recovery-Episode Controller

TQ-EMA v2 changed one controller property relative to v1. Confirmation of a valid downward recovery batch first applied the same bounded median-target recovery proposal and then entered a `RECOVERY_DOWN` episode. Authentication and access rules remained unchanged. Before a trusted update, the controller previewed the canonical EMA proposal. It skipped that proposal if either the profile mean or derived authentication threshold would increase; otherwise the bounded trusted transition was allowed.

An episode remained active for the next three distinct session-level adaptation observations and was refreshed by a new confirmed recovery batch. Resetting quarantine did not terminate an active episode. The v1 grid, caps, anchor, and trusted-path parameters were retained.

Fold-specific selection used synthetic validation replay only: clean \(D=0\) validation scores initialized and calibrated the profile, claimant observations used independently scored \(D=2\) validation transformations, and impostor checkpoints used \(D=0\). A configuration was feasible only when late-FAR increase was at most +1.0 percentage point and HTER degradation was at most +0.5 point. Selection failed closed if any fold lacked a feasible configuration.

## S5. Adaptive Quantile Profile

The Adaptive Quantile Profile replaced EMA moments with a discrete exponentially weighted empirical score distribution. Enrollment observations began with equal weights. For normalized non-negative weights, \(Q_p\) was the smallest observed score whose sorted cumulative weight was at least \(p\), without interpolation. The state retained \(q_{20}=Q_{0.20}\) and \(q_{50}=Q_{0.50}\). At enrollment,

\[
c=\frac{q_{50,0}-\tau_0}{q_{50,0}-q_{20,0}},
\qquad
\tau_t=q_{50,t}-c(q_{50,t}-q_{20,t}).
\]

The value of \(c\) was fixed and not clipped, making the initial quantile threshold equal to the validation-calibrated threshold within floating-point tolerance. A path was invalid when \(q_{50,0}-q_{20,0}<10^{-8}\). No fallback estimator or interpolation was introduced.

For an authorized observation \(s_t\), existing weights were multiplied by \(\rho\), \(s_t\) was appended with weight \(1-\rho\), weights were renormalized, and \(q_{20}\), \(q_{50}\), and the derived threshold were recomputed. Accepted-only Quantile updated only after authentication acceptance. Oracle-all Quantile made the same access decision but updated from every ground-truth genuine adaptation candidate; it was diagnostic and non-deployable.

The only tuned parameter was \(\rho\in\{0.80,0.90,0.95\}\); the quantile levels were fixed. Validation used the same claimant-only replay structure as TQ-EMA v2. Accepted-only Quantile alone determined feasibility and selection under the +1.0-point FAR and +0.5-point HTER limits. The branch failed closed if any fold lacked a feasible \(\rho\).

## S6. Branch-Specific Inference and Reproducibility

For TQ-EMA v1, each subject was averaged across available folds before paired percentile bootstrapping with 10,000 draws. A secondary victim-by-impostor-source bootstrap assessed late FAR, and a 99-subject complete-five-fold analysis checked the branch conclusion. Trusted and recovery event counts were audit totals rather than independent observations.

TQ-EMA v2 and Adaptive Quantile validation summaries are descriptive fold-level decision evidence, not outer inference. Their frozen packages are `results/paper3_tq_v2_validation_failed_20261001/` and `results/paper3_quantile_validation_failed_20261001_v1/`. TQ-EMA v1 results are in `results/paper3_tq_clean_drift_20261001_v1/`. No stopped branch was reopened during Reviewer Revision Round 2.
