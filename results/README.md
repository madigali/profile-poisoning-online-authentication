# Frozen results

The directories in this folder are completed, authoritative experiment
artifacts. Each retained run includes its configuration, exclusions, manifest,
and output tables. Validation-stopped methods explicitly record that outer test
data were not loaded.

| Directory | Role | Status |
|---|---|---|
| `paper3_attack_v2/` | Frozen versus Blind EMA poisoning baseline | Complete |
| `paper3_guarded_20260930/` | Guarded poisoning and lambda sweep | Complete |
| `paper3_oracle_all_drift_20261001_v2/` | Clean drift and selection-bias diagnostic | Complete |
| `paper3_tq_clean_drift_20261001_v1/` | Temporal quarantine v1 | Complete; no FRR recovery |
| `paper3_tq_v2_validation_failed_20261001/` | Recovery-episode v2 | Validation failed; outer test not loaded |
| `paper3_quantile_validation_failed_20261001_v1/` | Adaptive quantile branch | Validation failed; outer test not loaded |
| `paper3_final_analysis_20261002_v2/` | Final tables and three article figures | Complete |

Do not overwrite these directories. New diagnostic runs must use a new run ID.
