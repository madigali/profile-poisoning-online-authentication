# Paper 3 Attacker Capability Table

The boundary strategy is a **score-informed strong benchmark attacker**. It is not automatically white-box because it does not use model internals or gradients. The implementation assumes score access for candidate selection and does not demonstrate how a binary-feedback-only attacker would recover the same ranking.

| Capability / assumption | Paper 3 boundary attacker | Paper 3 random attacker | Deployment implication |
|---|---|---|---|
| Authentication decision observable | Yes | Yes | Both strategies assume attempts can be associated with an accept/reject outcome |
| Claimant score or confidence available | Yes, assumed for candidate selection | Not required for random selection | Boundary findings apply directly only where score access, leakage, or equivalent ranking information exists |
| Candidate pool available | Uses the preassigned test impostor poisoning pool | Uses the same type of preassigned pool | Acquisition of a comparable real-world candidate pool is outside the experiment |
| Candidate ranking | Initially accepted samples ordered by smallest non-negative margin to the initial threshold | Uniform random order without replacement | Boundary is deliberately stronger and more selective |
| Authentication threshold known | Operationally recoverable from score/margin selection in the experiment | Not needed for selection | A deployed attacker may not know the threshold |
| Reconnaissance / screening | Implicitly required to score and rank the pool | No score-based screening | Boundary reconnaissance burden is not measured |
| Poisoning budget (K) | Number of selected ranked attempts presented to the adaptive system | Number of selected random attempts presented | (K) is an update-phase presentation budget, not a total query budget |
| Candidate discovery counted in (K) | No | No separate discovery model | (K=8) must not be interpreted as an eight-query black-box attack |
| Total query cost measured | No | Presented attempts only | Attack efficiency per total real-world query is unknown |
| Timing | Selected sequence presented before the profile is frozen for future-probe evaluation | Same | The experiment isolates post-update state change, not continuous field interaction |
| Replay capability | Not used or evaluated | Not used or evaluated | Replay attacks remain out of scope |
| Model internals / weights | Not used | Not used | Boundary is score-access/gray-box-like, not necessarily white-box |
| Gradients | Not used | Not used | Gradient attacks remain out of scope |
| Ground-truth labels | Attacker uses dataset impostor membership for experimental construction; deployed label access is not assumed | Same experimental construction | Labels support evaluation; they are not an exposed production signal |
| Surrogate model | Not used | Not used | Surrogate ranking is not demonstrated |
| Sensor injection | Excluded | Excluded | Results do not cover forged sensor streams |
| Operating-system compromise | Excluded | Excluded | Results concern the online profile-update path, not full device compromise |
| Binary-feedback-only realization | Not demonstrated | Random strategy is compatible with no score ranking | A realistic binary-feedback boundary search remains future work |

## Scope statement

The attacks test whether accepted impostor observations can alter a frozen future decision state under the specified interfaces. They do not establish deployment prevalence, low-FAR vulnerability, or the total effort required to discover suitable candidates. The reported boundary effect is therefore a strong score-access benchmark for the update mechanism.
