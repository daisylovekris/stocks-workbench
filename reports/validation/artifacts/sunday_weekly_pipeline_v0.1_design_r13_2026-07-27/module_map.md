# r13 module map

| Path | Reused contract | Boundary |
|---|---|---|
| snapshots/rules/sunday_weekly_input_set_v0.1.schema.json | input-set schema identity | same-FD snapshot/final/no-op/orphan checks |
| snapshots/rules/sunday_weekly_input_set_v0.1.md | input-set contract identity | same-FD snapshot/final/no-op/orphan checks |
| snapshots/rules/sunday_weekly_pipeline_semantic_config_v0.1.json | daily_review_resolvers and raw identities | no guessed Daily Review directory |
| phase_b_actual_validator_execution.json | actual read-only Phase B validator execution | not a semantic input-set member |
| phase_c_authority_derivation_ledger.json | deterministic Phase C authority derivation | not named validator execution |
| snapshots/daily_review | true Daily Review raw SHA evidence | input-set member |
| snapshots/runtime/phase_c_summary | Phase C summary evidence | never a Daily Review |
| snapshots/runtime/phase_b_candidate | Phase B candidate evidence | never the SWP golden candidate |
| r13_static_state_validation.json | exact reason-set/static result | closure evidence only |
