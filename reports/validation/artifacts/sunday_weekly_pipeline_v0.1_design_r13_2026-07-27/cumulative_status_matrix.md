# r13 cumulative state/reason matrix

| State | reason_code | permissions |
|---|---|---|
| candidate_ready_for_human_review | candidate_created | human_review only; trading false |
| candidate_ready_for_human_review | all_gates_passed | human_review only; trading false |
| blocked_missing_facts | facts_missing:<date> | all false |
| blocked_invalid_facts | facts_validator_failed | all false |
| blocked_invalid_facts | facts_sha_drift | all false |
| blocked_invalid_facts | calendar_window_invalid | all false |
| blocked_invalid_facts | as_of_date_invalid | all false |
| blocked_invalid_facts | metrics_field_missing_or_invalid | all false |
| blocked_missing_daily_review | daily_review_missing:<date> | all false |
| blocked_future_data | future_input_detected | all false |
| blocked_future_data | source_time_unverifiable | all false |
| blocked_identity_conflict | identity_mismatch | all false |
| blocked_identity_conflict | legacy_review_sha_unverifiable | all false |
| blocked_identity_conflict | phase_b_evidence_missing | all false |
| blocked_identity_conflict | phase_b_evidence_invalid | all false |
| blocked_identity_conflict | phase_c_evidence_missing | all false |
| blocked_identity_conflict | phase_c_evidence_invalid | all false |
| blocked_identity_conflict | ambiguous_phase_c_authority | all false |
| blocked_identity_conflict | phase_c_state_invalid | all false |
| blocked_identity_conflict | phase_c_permission_invalid | all false |
| blocked_identity_conflict | candidate_schema_identity_invalid | all false |
| blocked_identity_conflict | candidate_semantics_identity_invalid | all false |
| blocked_identity_conflict | input_set_schema_identity_invalid | all false |
| blocked_identity_conflict | input_set_contract_identity_invalid | all false |
| blocked_identity_conflict | unsupported_symbol | all false |
| blocked_identity_conflict | unresolved_value_encoding_invalid | all false |
| blocked_identity_conflict | ambiguous_orphan_completion | all false |
| blocked_identity_conflict | forbidden_automatic_trading_field | all false |
| already_completed | valid_matching_completion | inherit original candidate; trading false |
| already_completed | index_recovered | inherit original candidate; trading false |
| no_candidate_for_window | no_trading_days | all false |
| failed | runtime_io_error | all false |
| failed | lock_error | all false |
| failed | unexpected_exception | all false |
