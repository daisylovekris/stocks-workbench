# Fully expanded cumulative finding mapping r9

| Finding ID | Severity | Final clause | State | reason_code | permissions | evidence | exact test ID |
|---|---|---|---|---|---|---|---|
| F-P2-1 | P2 | §2.1(3) | blocked_identity_conflict | legacy_review_sha_unverifiable | all false | review SHA | T01 |
| F-P2-2 | P2 | §2.1(1) | blocked_invalid_facts | calendar_window_invalid | all false | coverage SHA | T02 |
| F-P2-3 | P2 | §2.1(4) | blocked_invalid_facts | metrics_field_missing_or_invalid | all false | metrics fields | T03 |
| F-P2-4 | P2 | §5 | already_completed | index_recovered | trading false | live evidence | T04 |
| F-P3-1 | P3 | §4 | new run | input_set_changed | no upgrade | input identity | T05 |
| F-P3-2 | P3 | §2.1(5) | blocked_future_data | source_time_unverifiable | all false | config registry | T06 |
| F-P3-3 | P3 | §2.1(1) | blocked_invalid_facts | as_of_date_invalid | all false | request envelope | T07 |
| F-P3-4 | P3 | §4 | failed | lock_error | all false | atomic diagnostic | T08 |
| L-r2-calendar | P2 | §2.1(1) | blocked_invalid_facts | calendar_window_invalid | all false | coverage | T09 |
| L-r2-phasec | P3 | G7 | blocked_identity_conflict | phase_c_state_invalid | all false | state enum | T10 |
| L-r3-request | P2 | §4 | failed | diagnostics | all false | request key | T11 |
| L-r3-completion | P2 | §5 | blocked_identity_conflict | ambiguous_orphan_completion | all false | orphan inventory | T12 |
| L-r4-sealing | P2 | package algorithm | sealed | package SHA | n/a | manifest | T13 |
| L-r5-evidence | P2 | G4 | blocked_identity_conflict | phase_b_evidence_invalid | all false | raw SHA | T14 |
| L-r6-authority | P2 | §2.1(7-8) | blocked_identity_conflict | phase_c_evidence_invalid | all false | index chain | T15 |
| L-r7-safe-read | P2 | §2.1(7) | blocked_identity_conflict | phase_c_evidence_invalid | all false | same FD | T16 |
| L-r8-concurrency | P2 | §6 | blocked_identity_conflict | ambiguous_phase_c_authority | all false | final resolver | T17 |
| R9-schema | P2 | schema/config | blocked_identity_conflict | candidate_schema_identity_invalid | all false | schema FD SHA | T18 |
