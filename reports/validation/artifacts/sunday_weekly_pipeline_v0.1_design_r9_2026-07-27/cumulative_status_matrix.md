# Fully expanded status matrix r9

| State | reason_code | permissions | evidence |
|---|---|---|---|
| blocked_invalid_facts | calendar_window_invalid/as_of_date_invalid/metrics_field_missing_or_invalid | all false | calendar/fields |
| blocked_future_data | future_input_detected/source_time_unverifiable | all false | registry/cutoff |
| blocked_identity_conflict | legacy_review_sha_unverifiable | all false | review SHA |
| blocked_identity_conflict | phase_b_evidence_missing/phase_b_evidence_invalid | all false | runner chain |
| blocked_identity_conflict | phase_c_evidence_missing/phase_c_evidence_invalid/phase_c_state_invalid/ambiguous_phase_c_authority | all false | index/manifest |
| blocked_identity_conflict | candidate_schema_identity_invalid | all false | same-FD schema SHA |
| failed | lock_error/runtime_io_error | all false | diagnostics |
| already_completed | valid_matching_completion/index_recovered | trading false | full revalidation |
| candidate_ready_for_human_review | all_gates_passed | human_review only | sealed inputs |
