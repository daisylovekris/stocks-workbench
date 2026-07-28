# Complete r1-r8 finding mapping

| Finding ID | Severity | Final clause | State/reason | Permissions | Evidence | Exact tests |
|---|---|---|---|---|---|---|
| F-P2-1 legacy review SHA | P2 | §2.1(3) | identity conflict / legacy_review_sha_unverifiable | all false | review bytes/SHA | F01 |
| F-P2-2 calendar cross-year | P2 | §2.1(1) | invalid facts/calendar_window_invalid | all false | coverage SHA | F02 |
| F-P2-3 partial whitelist | P2 | §2.1(4) | metrics invalid | all false | field diagnostic | F03 |
| F-P2-4 index recovery | P2 | §5 | recovered/no-op | no trading | live revalidation | F04 |
| F-P3-1 semantic no-op | P3 | §4 | new input set | unchanged | input identity | F05 |
| F-P3-2 time | P3 | §2.1(5)+config | future blocked | all false | registry/time | F06,T01 |
| F-P3-3 Shanghai date | P3 | §2.1(1) | as_of invalid | all false | request envelope | F07 |
| F-P3-4 diagnostics | P3 | §4 | atomic diagnostic | all false | attempt path | F08 |
| L-r2/r3 identity/calendar | P2/P3 | §§1,4,5 | defined blockers | all false | resolver identities | L01-L04 |
| L-r4/r5 sealing/config | P2 | config+package | new input set | no upgrade | raw SHA | L05-L06 |
| L-r6 authority | P2 | §2.1(7-8) | phase evidence blockers | all false | index/runner chain | L07-L09 |
| L-r7 safe resolver | P2 | §2.1(7) | phase_c invalid | all false | same-FD bytes | L10-L12 |
| R8 candidate schema | P2 | schema+config | input set change | no upgrade | schema raw SHA | R01-R02 |
| R8 authority window | P2 | §6 | ambiguous authority | all false | final resolver | R03-R07 |
