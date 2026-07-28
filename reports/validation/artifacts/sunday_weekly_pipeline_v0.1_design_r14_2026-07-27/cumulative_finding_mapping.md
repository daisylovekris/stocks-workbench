# r14 fully expanded cumulative finding mapping

| Finding ID | Severity | Final clause | state | outcome | reason_code | permissions | Evidence | Exact test ID |
|---|---|---|---|---|---|---|---|---|
| Fable-P2-1 | P2 | §2.1.3 review identity | blocked_identity_conflict | blocked | legacy_review_sha_unverifiable | all false | review bytes | T01 |
| Fable-P2-2 | P2 | §2.1 calendar coverage | blocked_invalid_facts | blocked | calendar_window_invalid | all false | calendar snapshot | T02 |
| Fable-P2-3 | P2 | §2.1.4 partial facts | blocked_invalid_facts | blocked | metrics_field_missing_or_invalid | all false | facts snapshot | T07 |
| Fable-P2-4 | P2 | §6 recovery | already_completed | no_op | index_recovered | inherit original candidate; trading false | completion evidence | T24 |
| Fable-P3-1 | P3 | §6 matching completion | already_completed | no_op | valid_matching_completion | inherit original candidate; trading false | input identity | T20 |
| Fable-P3-2 | P3 | §2.1.5 time registry | blocked_future_data | blocked | source_time_unverifiable | all false | config snapshot | T27 |
| Fable-P3-3 | P3 | §3 request envelope | blocked_invalid_facts | blocked | as_of_date_invalid | all false | envelope | T11 |
| Fable-P3-4 | P3 | §6 diagnostics | failed | failed | lock_error | all false | atomic evidence | T12 |
| Lucien-r2-calendar | P2 | §2.1 coverage contract | blocked_invalid_facts | blocked | calendar_window_invalid | all false | calendar raw SHA | T03 |
| Lucien-r2-phase-c | P2 | §2.1 Phase C enum | blocked_identity_conflict | blocked | phase_c_state_invalid | all false | review manifest | T09 |
| Lucien-r2-diagnostic | P2 | §6 diagnostics | failed | failed | lock_error | all false | unique attempt ID | T12 |
| Lucien-r3-request | P2 | §3 request_key | blocked_invalid_facts | blocked | as_of_date_invalid | all false | envelope | T11 |
| Lucien-r3-completion | P2 | §6 physical completion | blocked_identity_conflict | blocked | ambiguous_orphan_completion | all false | completion index | T25 |
| Lucien-r3-time | P2 | §2.1.5 cutoff | blocked_future_data | blocked | source_time_unverifiable | all false | time fields | T26 |
| Lucien-r4-sealing | P2 | package algorithm | blocked_identity_conflict | blocked | identity_mismatch | all false | manifests | T36 |
| Lucien-r4-mapping | P2 | closure matrices | blocked_identity_conflict | blocked | identity_mismatch | all false | local matrices | T36 |
| Lucien-r4-time | P2 | config registry | blocked_future_data | blocked | source_time_unverifiable | all false | config bytes | T27 |
| Lucien-r4-envelope | P2 | §3 safe envelope | blocked_invalid_facts | blocked | as_of_date_invalid | all false | redacted envelope | T11 |
| Lucien-r4-lock | P2 | §6 lock contract | failed | failed | lock_error | all false | lock path | T29 |
| Lucien-r5-input-set | P2 | §3 input set | blocked_identity_conflict | blocked | identity_mismatch | all false | raw SHA ledger | T20 |
| Lucien-r5-phase-evidence | P2 | §2.1 authority | blocked_identity_conflict | blocked | phase_b_evidence_missing | all false | expected/actual paths | T13 |
| Lucien-r5-golden | P2 | candidate semantics | candidate_ready_for_human_review | candidate_created | all_gates_passed | human_review only | golden inputs | T35 |
| Lucien-r5-lock-order | P2 | §6 lock order | failed | failed | lock_error | all false | order evidence | T29 |
| Lucien-r6-resolver | P2 | §2.1 Phase C resolver | blocked_identity_conflict | blocked | phase_c_evidence_invalid | all false | index/manifest chain | T17 |
| Lucien-r6-phase-b | P2 | §2.1 Phase B resolver | blocked_identity_conflict | blocked | phase_b_evidence_invalid | all false | runner manifest | T14 |
| Lucien-r6-rebuild | P2 | §2.1 rebuild policy | blocked_identity_conflict | blocked | phase_b_evidence_missing | all false | provenance | T19 |
| Lucien-r6-config | P2 | semantic config | blocked_identity_conflict | blocked | identity_mismatch | all false | raw config SHA | T21 |
| Lucien-r7-safe-read | P2 | §2.1 same-FD read | blocked_identity_conflict | blocked | phase_c_evidence_invalid | all false | safe-read snapshot | T18 |
| Lucien-r7-time-grammar | P2 | config grammar | blocked_future_data | blocked | source_time_unverifiable | all false | registry | T27 |
| Lucien-r7-candidate-gate | P2 | §2.1 Phase C gate | blocked_identity_conflict | blocked | phase_c_evidence_invalid | all false | candidate metadata | T17 |
| Lucien-r7-path-boundary | P2 | §3 runtime token boundary | blocked_identity_conflict | blocked | identity_mismatch | all false | rule snapshot | T29 |
| Lucien-r8-package | P2 | package algorithm | blocked_identity_conflict | blocked | identity_mismatch | all false | manifests | T36 |
| Lucien-r8-schema | P2 | candidate schema | blocked_identity_conflict | blocked | candidate_schema_identity_invalid | all false | schema SHA | T22 |
| Lucien-r8-concurrency | P2 | §6 final lock window | blocked_identity_conflict | blocked | ambiguous_phase_c_authority | all false | locked resolver | T29 |
| Lucien-r9-decimal | P2 | candidate schema decimals | blocked_identity_conflict | blocked | candidate_schema_identity_invalid | all false | AJV output | T30 |
| Lucien-r9-schema-binding | P2 | §2.1 schema identity | blocked_identity_conflict | blocked | candidate_schema_identity_invalid | all false | same-FD SHA | T22 |
| Lucien-r9-review-lock | P2 | §6 review lock source | failed | failed | lock_error | all false | module map | T29 |
| Lucien-r9-matrix | P2 | closure matrices | blocked_identity_conflict | blocked | identity_mismatch | all false | local matrices | T36 |
| Lucien-r10-decimal | P2 | schema decimal families | blocked_identity_conflict | blocked | candidate_schema_identity_invalid | all false | AJV output | T30 |
| Lucien-r10-safe-value | P2 | candidate schema safe_value | blocked_identity_conflict | blocked | candidate_schema_identity_invalid | all false | schema snapshot | T32 |
| Lucien-r10-semantics | P2 | candidate semantics | blocked_identity_conflict | blocked | candidate_semantics_identity_invalid | all false | semantics SHA | T23 |
| Lucien-r10-golden | P2 | golden derivation | candidate_ready_for_human_review | candidate_created | all_gates_passed | human_review only | golden candidate | T34 |
| R11-decimal-regex | P2 | schema `$defs` | blocked_identity_conflict | blocked | candidate_schema_identity_invalid | all false | AJV draft-2020 record | T30 |
| R11-unresolved-source | P2 | candidate semantics | candidate_ready_for_human_review | candidate_created | all_gates_passed | human_review only | five Phase C manifests | T33 |
| R11-semantics-identity | P2 | §2.1.10 | blocked_identity_conflict | blocked | candidate_semantics_identity_invalid | all false | same-FD SHA | T23 |
| R11-input-set | P2 | §3 input-set algorithm | candidate_ready_for_human_review | candidate_created | all_gates_passed | human_review only | input-set ledger | T35 |
| R12-candidate-bytes | P2 | candidate canonical bytes | already_completed | no_op | valid_matching_completion | inherit original candidate; trading false | raw bytes/manifest | T37 |
| R12-true-daily-review | P2 | input-set contract | candidate_ready_for_human_review | candidate_created | all_gates_passed | human_review only | five review SHA values | T39 |
| R12-input-schema | P2 | §2.1.10/§4 | blocked_identity_conflict | blocked | input_set_schema_identity_invalid | all false | same-FD schema evidence | T38 |
| R12-live-evidence | P2 | Phase B/C audit evidence | blocked_identity_conflict | blocked | phase_c_evidence_invalid | all false | validation snapshots | T40 |
| R12-matrix-sync | P2 | §7 | already_completed | no_op | valid_matching_completion | inherit original candidate; trading false | static audit | T41 |
| R12-ajv-record | P3 | candidate schema | blocked_identity_conflict | blocked | candidate_schema_identity_invalid | all false | fixtures/execution log | T42 |
| R13-input-contract | P2 | input-set contract | blocked_identity_conflict | blocked | input_set_contract_identity_invalid | all false | same-FD contract SHA | T43 |
| R13-daily-resolver | P2 | daily_review_resolvers | blocked_identity_conflict | blocked | unsupported_symbol | all false | semantic config/resolver | T44 |
| R13-phase-b-execution | P2 | Phase B evidence | blocked_identity_conflict | blocked | phase_b_evidence_invalid | all false | actual validator execution | T45 |
| R13-phase-c-ledger | P2 | Phase C evidence | blocked_identity_conflict | blocked | phase_c_evidence_invalid | all false | derivation ledger | T46 |
| R13-unresolved-number | P2 | input-set contract | blocked_identity_conflict | blocked | unresolved_value_encoding_invalid | all false | schema/contract | T47 |
| R13-zero-trading | P2 | window terminal state | no_candidate_for_window | no_candidate | no_trading_days | all false | calendar diagnostic | T48 |
| R13-state-sync | P2 | §7 matrix | already_completed | no_op | valid_matching_completion | inherit original candidate; trading false | static set-diff output | T49 |
| R13-state-candidate-created | P3 | §7 full state coverage | candidate_ready_for_human_review | candidate_created | all_gates_passed | human_review only | state matrix | T49 |
| R13-state-facts-missing:date | P3 | §7 full state coverage | blocked_missing_facts | blocked | facts_missing:<date> | all false | state matrix | T49 |
| R13-state-facts-validator-failed | P3 | §7 full state coverage | blocked_invalid_facts | blocked | facts_validator_failed | all false | state matrix | T49 |
| R13-state-facts-sha-drift | P3 | §7 full state coverage | blocked_invalid_facts | blocked | facts_sha_drift | all false | state matrix | T49 |
| R13-state-daily-review-missing:date | P3 | §7 full state coverage | blocked_missing_daily_review | blocked | daily_review_missing:<date> | all false | state matrix | T49 |
| R13-state-future-input-detected | P3 | §7 full state coverage | blocked_future_data | blocked | future_input_detected | all false | state matrix | T49 |
| R13-state-phase-c-evidence-missing | P3 | §7 full state coverage | blocked_identity_conflict | blocked | phase_c_evidence_missing | all false | state matrix | T49 |
| R13-state-phase-c-permission-invalid | P3 | §7 full state coverage | blocked_identity_conflict | blocked | phase_c_permission_invalid | all false | state matrix | T49 |
| R13-state-forbidden-automatic-trading-field | P3 | §7 full state coverage | blocked_identity_conflict | blocked | forbidden_automatic_trading_field | all false | state matrix | T49 |
| R13-state-runtime-io-error | P3 | §7 full state coverage | failed | failed | runtime_io_error | all false | state matrix | T49 |
| R13-state-unexpected-exception | P3 | §7 full state coverage | failed | failed | unexpected_exception | all false | state matrix | T49 |
