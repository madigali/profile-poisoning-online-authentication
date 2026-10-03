# Attack Eligibility Summary

Boundary (K=8) requires enough impostor candidates to be accepted by the initial authentication threshold. The reported boundary estimates are therefore conditional on maximum-budget feasibility.

## Cohort summary

| Dataset | Strategy | Subjects overall | Victim-fold combinations | Repeats | Possible paths | (K=8) eligible paths | (K=8) excluded paths | Unique eligible victims | Effective subject (n) | Are all possible (K=0) paths retained? | Pool separation |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| HMOG | Boundary | 100 | 500 | 100 | 50,000 | 49,889 | 111 | 100 | 100 | No; common (K=8)-feasible cohort | Source-session groups disjoint; source identity can occur in both pools |
| HMOG | Random | 100 | 500 | 100 | 50,000 | 49,889 | 111 | 100 | 100 | No; same common cohort as boundary | Source-session groups disjoint; source identity can occur in both pools |
| McGill | Boundary | 20 | N/A | 100 | 2,000 | 1,456 | 544 | 18 | 18 | No; maximum-budget-feasible cohort | Source identities disjoint between poison and probe pools |
| McGill | Random | 20 | N/A | 100 | 2,000 | 2,000 | 0 | 20 | 20 | Yes | Source identities disjoint between poison and probe pools |

## Exclusions by available initially accepted candidates

| Dataset / strategy cohort | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | Total excluded |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HMOG common boundary-feasible cohort | 0 | 1 | 1 | 3 | 13 | 22 | 31 | 40 | 111 |
| McGill boundary | 280 | 88 | 49 | 31 | 42 | 21 | 28 | 5 | 544 |
| McGill random | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The HMOG implementation established one common paired cohort before evaluating either strategy. If a path lacked eight initially accepted boundary candidates, both its random and boundary outputs were omitted at every (K), including (K=0). This keeps HMOG strategy comparisons paired but means that random and baseline summaries are conditional on boundary feasibility.

The McGill implementation retained all 2,000 random paths. Boundary summaries, including boundary (K=0), used the 1,456 paths that could support (K=8). Two McGill victims had no eligible boundary path; the reported boundary effect therefore uses 18 victims.

## Interpretation

Requiring enough initially accepted boundary candidates can produce feasibility-selection bias: victims or paths with more false accepts may be overrepresented in the maximum-budget boundary estimate. The present records establish the conditioning and its extent, but they do not establish the direction or magnitude of bias relative to all possible paths. The manuscript therefore reports eligibility explicitly and does not generalize the conditional (K=8) effect to every enrolled user or deployment.

Machine-readable counts are in `paper/attack_eligibility_summary.csv`. All values were derived from frozen retained `by_fold`, `attack_subject_repeat`, and exclusion records; no attack path was regenerated.
