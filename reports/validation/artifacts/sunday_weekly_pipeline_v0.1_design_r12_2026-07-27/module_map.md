# r12 module map

| Path | Bytes | SHA-256 | Reused contract | Boundary |
|---|---:|---|---|---|
| snapshots/rules/sunday_weekly_input_set_v0.1.schema.json | 1312 | 2bf047907dabf0006c60aa8934b8a64a020040f3c120d95839ebc427cf6634a1 | input-set identity | same-FD config match |
| phase_b_live_validation.json | 5960 | e938c6ac0529b4c97f45784c97659b30ec64ae059a8569a57427ff2af48ac90c | Phase B audit | evidence snapshot only |
| phase_c_authority_validation.json | 8599 | 50d5f9a6978ce82509709340ec0565727d3f6c452a921354d0acf22483c1aed6 | Phase C authority audit | evidence snapshot only |
| snapshots/daily_review/sungrow_review_2026-07-20.md | 7716 | 537ff5e5612e65a713e30afa44107cb33b2cc52eef350d306add50ba91478964 | true Daily Review | input-set member |
| snapshots/daily_review/sungrow_review_2026-07-21.md | 7998 | 6a5a829644379204efb9e528be6d408435acca1bdeade1a872c6073aaa560f7a | true Daily Review | input-set member |
| snapshots/daily_review/sungrow_review_2026-07-22.md | 7692 | 4eed915f06d64f10108938c2935ce6e49b69cb573f28e18744c2a78f421efad4 | true Daily Review | input-set member |
| snapshots/daily_review/sungrow_review_2026-07-23.md | 6000 | 67973ddd7c635c61d29d2583a104b6a2e911de1b1494d7fd19c4889b18a07b13 | true Daily Review | input-set member |
| snapshots/daily_review/sungrow_review_2026-07-24.md | 6246 | 7314f1ce4a3884b2222d40ee784a993534c6a6e5c96c28237ae10879577d718f | true Daily Review | input-set member |
| snapshots/runtime/phase_b_candidate/2026-07-20.candidate.json through 2026-07-24.candidate.json | see file manifest | Phase B candidate evidence | audit only, not SWP candidate |
| snapshots/tools/safe_file_read.py | see file manifest | same-FD bytes/SHA/parse | no alternate read path |
| snapshots/tools/review_manifest.py | see file manifest | review_lock_path/Phase C validation | no copied hash algorithm |
| snapshots/tools/phase_b_completion.py | see file manifest | completion manifest validation | no runner scanning |
