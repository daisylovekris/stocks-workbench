# r11 cumulative state and reason matrix

| State | reason_code | Permissions | Evidence |
|---|---|---|---|
| blocked_invalid_facts | calendar_window_invalid | all false | calendar raw SHA/coverage finding |
| blocked_invalid_facts | metrics_field_missing_or_invalid | all false | facts raw SHA/path |
| blocked_future_data | source_time_unverifiable | all false | registry/path finding |
| blocked_identity_conflict | legacy_review_sha_unverifiable | all false | review bytes/missing facts SHA |
| blocked_identity_conflict | phase_b_evidence_missing | all false | expected/actual runner evidence |
| blocked_identity_conflict | phase_b_evidence_invalid | all false | runner schema/identity finding |
| blocked_identity_conflict | phase_c_evidence_missing | all false | index candidates/missing authority |
| blocked_identity_conflict | phase_c_evidence_invalid | all false | candidate/manifest violation |
| blocked_identity_conflict | ambiguous_phase_c_authority | all false | conflicting valid authorities |
| blocked_identity_conflict | phase_c_state_invalid | all false | observed state |
| blocked_identity_conflict | candidate_schema_identity_invalid | all false | same-FD schema SHA |
| blocked_identity_conflict | candidate_semantics_identity_invalid | all false | same-FD semantics SHA |
| blocked_identity_conflict | ambiguous_orphan_completion | all false | validated orphan set |
| failed | lock_error | all false | atomic diagnostic attempt path |
| already_completed | index_recovered | all false | live full revalidation/index repair |
| already_completed | semantic_noop | all false | exact semantic completion/index |
| candidate_ready_for_human_review | all_gates_passed | human review only | complete input set/candidate bytes |
