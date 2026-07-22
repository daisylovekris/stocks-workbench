# Six-day Phase C Review Manifest Validation — 2026-07-22

## Scope and model gate

- Scope: generate only repository-external Phase C deterministic review artifacts for 300274 on 2026-07-15, 07-16, 07-17, 07-20, 07-21, and 07-22; no official facts, review, current-card, index, weekly, or Phase A/B/C code write.
- Session rollout: `/Users/wongdaisy/.codex/sessions/2026/07/22/rollout-2026-07-22T23-39-08-019f8a7b-0ee1-74d1-adbd-5398f0b19035.jsonl`.
- Actual `turn_context`: `model=gpt-5.6-terra`; `effort=medium` (gate passed before work).
- Runtime root (resolved): `/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime`; it is outside `/Users/wongdaisy/Mimo-Lab/stocks`, and `find -type l` returned no alias.
- Calendar SHA-256: `fd693d1e62b46408e7fbff3049e06cd368e5026279398d0c5e5344e3472add5e` (`config/a_share_trading_calendar_2026.json`).

## Inputs and live facts validation

Each canonical `data/daily/300274_<date>_facts.json` was read live and passed `tools.validate_review_chain.assert_facts_pack_valid`; no prior validation report was used as a data source.

| trade_date | official SHA-256 | live facts Validator | matching runner manifest |
|---|---|---|---|
| 2026-07-15 | `0ae94a7d612d2f7c5a35a5f06b5f7e44a4ced95c7f55b89fa049339b5b57c00f` | PASS | `runs/2026-07-15/986e7218-79a4-4a03-985c-5bb9c5831d4c/manifest.json` |
| 2026-07-16 | `430c05a685712a22ed362a34b7fdaad0bbd843529663b39bc89db741b0ac0984` | PASS | `runs/2026-07-16/6c1cb1cd-c64d-4905-93fa-8ca893364d94/manifest.json` |
| 2026-07-17 | `74731d190a1946df1b79f580c498d2a57b4a191c8d3f8415d8fe9b953e2ab1bd` | PASS | `runs/2026-07-17/a7800288-8563-418b-b329-7f2a838c11f4/manifest.json` |
| 2026-07-20 | `4ef128d6314383f40263b6cba137ae10a9e7fc5d3353ef109db666e6978b1460` | PASS | `runs/2026-07-20/b8fe6419-6ca6-48b1-94e2-713112d94753/manifest.json` |
| 2026-07-21 | `d5049f43f612744558c5e572938e49c60650657991c339627cade2979b3fc071` | PASS | `runs/2026-07-21/eafa878c-a098-464b-a39c-8d24422c1128/manifest.json` |
| 2026-07-22 | `795a4e77a84fcdebfd5f2f52b088728d86c20833c0d33318c3687298e30ab30a` | PASS | `runs/2026-07-22/fcc609d0-04b1-47e2-b1c5-d8f9ab03fef0/manifest.json` |

All six selected Phase B manifests are schema-valid, repository-external non-symlink files with the canonical recorded manifest path; `symbol=300274`, matching `target_date`, `stage=finished`, non-null `finished_at`, `write_official=true`, `dry_run=false`, `write_action=created`, `outcome=partial`, `reason_code=official_written_partial`, `official_changed=true`, and matching candidate/after/current official SHA. Candidate, post-write Validator, and write evidence are present. The manifest bytes were individually hashed and passed the Phase C runner gate. A sensitive-pattern scan found no Authorization/Cookie/Bearer/key/token/password material in these six runner manifests.

## Per-date Phase C output

All paths below are rooted at `/Users/wongdaisy/Library/Application Support/Mimo-Lab/stocks-runtime`.

| trade_date | official_path / SHA | facts_validator | runner path / SHA | runner action / outcome / reason | review_type / state / review_id | review manifest / SHA | summary / index entry | downstream permissions | second run | blocker |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-07-15 | `data/daily/300274_2026-07-15_facts.json` / `0ae94a7d…7c00f` | PASS | `runs/2026-07-15/986e7218-79a4-4a03-985c-5bb9c5831d4c/manifest.json` / `dc572d52…3227e` | created / partial / official_written_partial | facts_review / needs_manual_review / `rev_300274_2026-07-15_0ae94a7d612d2f7c` | `reviews/2026-07-15/rev_300274_2026-07-15_0ae94a7d612d2f7c/review_manifest.json` / `cadd191d…52e3a` | sibling `review_summary.md`; `reviews/2026-07-15/review_index.jsonl` (one line) | all false | review_already_exists | none |
| 2026-07-16 | `data/daily/300274_2026-07-16_facts.json` / `430c05a6…c0984` | PASS | `runs/2026-07-16/6c1cb1cd-c64d-4905-93fa-8ca893364d94/manifest.json` / `9a5387a1…a5b19` | created / partial / official_written_partial | facts_review / needs_manual_review / `rev_300274_2026-07-16_430c05a685712a22` | `reviews/2026-07-16/rev_300274_2026-07-16_430c05a685712a22/review_manifest.json` / `f7a0087c…e9121` | sibling `review_summary.md`; `reviews/2026-07-16/review_index.jsonl` (one line) | all false | review_already_exists | none |
| 2026-07-17 | `data/daily/300274_2026-07-17_facts.json` / `74731d19…ab1bd` | PASS | `runs/2026-07-17/a7800288-8563-418b-b329-7f2a838c11f4/manifest.json` / `962ccbc5…e5b0c` | created / partial / official_written_partial | facts_review / needs_manual_review / `rev_300274_2026-07-17_74731d190a1946df` | `reviews/2026-07-17/rev_300274_2026-07-17_74731d190a1946df/review_manifest.json` / `e81d230e…07955b` | sibling `review_summary.md`; `reviews/2026-07-17/review_index.jsonl` (one line) | all false | review_already_exists | none |
| 2026-07-20 | `data/daily/300274_2026-07-20_facts.json` / `4ef128d6…b1460` | PASS | `runs/2026-07-20/b8fe6419-6ca6-48b1-94e2-713112d94753/manifest.json` / `853886f6…21387` | created / partial / official_written_partial | facts_review / needs_manual_review / `rev_300274_2026-07-20_4ef128d6314383f4` | `reviews/2026-07-20/rev_300274_2026-07-20_4ef128d6314383f4/review_manifest.json` / `cd7a6035…90122` | sibling `review_summary.md`; `reviews/2026-07-20/review_index.jsonl` (one line) | all false | review_already_exists | none |
| 2026-07-21 | `data/daily/300274_2026-07-21_facts.json` / `d5049f43…fc071` | PASS | `runs/2026-07-21/eafa878c-a098-464b-a39c-8d24422c1128/manifest.json` / `7773ec4e…77478` | created / partial / official_written_partial | facts_review / needs_manual_review / `rev_300274_2026-07-21_d5049f43f6127445` | `reviews/2026-07-21/rev_300274_2026-07-21_d5049f43f6127445/review_manifest.json` / `85d0ffe3…5c671` | sibling `review_summary.md`; `reviews/2026-07-21/review_index.jsonl` (one line) | all false | review_already_exists | none |
| 2026-07-22 | `data/daily/300274_2026-07-22_facts.json` / `795a4e77…ab30a` | PASS | `runs/2026-07-22/fcc609d0-04b1-47e2-b1c5-d8f9ab03fef0/manifest.json` / `4496ecf4…4b34c` | created / partial / official_written_partial | facts_review / needs_manual_review / `rev_300274_2026-07-22_795a4e77a84fcdeb` | `reviews/2026-07-22/rev_300274_2026-07-22_795a4e77a84fcdeb/review_manifest.json` / `fce2bcaf…cf008` | sibling `review_summary.md`; `reviews/2026-07-22/review_index.jsonl` (one line) | all false | review_already_exists | none |

`all false` is the implementation's permanent permission object: `review`, `current_cards`, `index`, `weekly`, `git`, and `trading` are all `false`; it leaves daily-review/current-card/workbench-index/weekly/trade actions unavailable. Each record's `review_index.jsonl` entry was read back, schema-validated, and cross-checked against its manifest path, review ID, official SHA, manifest SHA, and state. No duplicate index row, manifest, or fingerprint exists.

Full runtime artifact SHA-256 values:

| trade_date | runner_manifest_sha256 | review_manifest_sha256 |
|---|---|---|
| 2026-07-15 | `dc572d528ad92ad06919a3e188c11e0e79f14dae51e920b126aacc49d933227e` | `cadd191d33f50f75a98942e398c9332eac89e096948d9851049fac6fa0f52e3a` |
| 2026-07-16 | `9a5387a1a12779a20983bdcefece0b1d8af8c8c3f76d78a7685554724a0a5b19` | `f7a0087c4a0c777885966f1dda80da68a672981ec31614cbf20e35d289ae9121` |
| 2026-07-17 | `962ccbc586aadb9163f3561e26d2c34715aa9d6deff27e2c472bd4b42e1e5b0c` | `e81d230e75b4ebc7f1d91722d2acf61ae0c885448d955cdfbfa27eb13f07955b` |
| 2026-07-20 | `853886f6632857231374d156c71ac3f6c6fc58516af7c75a62d50371b5521387` | `cd7a603504be41cee7df1670fed65a09f7fc2b16507cac19f1a0912314790122` |
| 2026-07-21 | `7773ec4e07a59ae1ee733420ead083ded48d988fa6c6a186e9811ca444477478` | `85d0ffe38d2e3e0f56837476ce1e005b2f8677350b9bf234b9146e147b35c671` |
| 2026-07-22 | `4496ecf4f8596f6bc0fb85b961bbb8dc435ad6cedd3dbb2d392cd15731b4b34c` | `fce2bcaf88759ef5fc2d00bb793c9fdb401889c6f6e77263a94fcb244c6cf008` |

## Classification and daily-review handoff boundary

- `facts_review`: all six dates.
- `incident_review`: none.
- `ready_for_human_review`: none.
- `needs_manual_review`: all six dates.
- The six facts packs are `partial`; each has the same four unresolved manual fields: `disclosure_status`, `market_indices`, `news_policy_context`, and `sector_context`. Confirmed structured fields are quote open/high/low/close/prev_close/pct_change/amount/turnover_rate and `volume_ratio`.
- Input to any later daily-review task is restricted to the canonical official facts and its matching Phase C manifest above. It must retain those four unresolved fields and cannot infer them from old reviews, cards, weekly, archive reports, or this report.
- There is no `weekly/*2026-07-19*` file in this checkout. A later 07-19 weekly task therefore needs an explicitly supplied weekly target/template and may use only its authorized facts inputs; this Phase C run created no weekly input or output.

## Regression and protected-material checks

- Six live facts Validators: PASS.
- Phase C targeted regression: `python3 -m pytest -q tests/test_review_manifest.py` → `122 passed` (includes Phase B semantic matrix, invalid-runner incident, idempotency, index recovery/alias conflict, and sensitive filtering coverage).
- 2026-07-13 and 2026-07-14 live facts Validator: PASS; their review Validators: PASS, P0/P1/P2/P3 all zero.
- Protected SHA-256 before and after (unchanged): reviews `sungrow_review_2026-07-13.md=9dd9f7403bd97e29997beccbd4e541a134281e2acae2d9ee38b23f9f1a57662f`, `sungrow_review_2026-07-14.md=0941e43cdf4be34f8d7bb71d0fa4a0f9e1bb69d3b2f48e19f80fe07869f87392`; five current cards `fb70ecc64ea0d5d2f5c8d4e6a9bef723899177c2fa71d6db13d9f9e1abc7ca2d`, `51f60bfa341efe0993ff0a7d92c34eae64623403c09dda666237d0d5d5f942ed`, `cb56c4a8897889b5c4c2b6e0beef2eda7aa8870b21bf2f85dafe5e255021decc`, `0a6374248f2c653c96d397ebb2e79c3360f0c603fbaf31316ae36c24dce04c81`, `be8d46aad87514a3cfa4d84bb60d7625179301344ce42f884cef43ce2e3aa9ae`; `stock_workbench_index.md=d85c3e5cdd9feeb5796b34e38fbc8a7b18994d22164af37eada16622491c90f6`. Existing weekly files were likewise unchanged; no 2026-07-19 weekly file exists.
- Six official facts SHA-256 values in the input table were rechecked after generation and unchanged.
- `git diff --check`: PASS. `git diff --cached --check`: PASS.

## Git and findings

Initial worktree already contained user changes: `M tests/test_codex_auto_routing.sh`, `M tools/codex-auto.sh`, `?? repo_harness_readonly_research_notes.md`, and `?? rules/fable_phase_c_external_review_v0.1.md`. This run added only this untracked report; no `git add`, commit, push, or other Git write was performed.

- P1: none in this run.
- P2: `rules/review_manifest_phase_c_v0.2.md` section 1 still says Phase C does not handle `2026-07-15`, whereas the current implementation accepts it and this explicitly authorized run generated a valid 07-15 manifest. This is a documentation/operational-scope inconsistency; no code or rule file was changed under this task boundary.

### P2 resolution

- Rule change: `rules/review_manifest_phase_c_v0.2.md` section 1 removed the hard-coded `2026-07-15` exclusion and now limits Phase C to explicitly authorized official-calendar trading days. It requires existing canonical official facts, a live facts Validator PASS, a legal matching-current-SHA Phase B runner manifest, semantic-matrix validation of `write_action` / `outcome` / `reason_code`, and an in-lock final official-SHA recheck. Arbitrary dates, stale manifests, and archive reports remain prohibited inputs.
- 2026-07-15 gate evidence: it is present in the repaired official trading calendar; the canonical facts file exists with SHA-256 `0ae94a7d612d2f7c5a35a5f06b5f7e44a4ced95c7f55b89fa049339b5b57c00f`; the live facts Validator passes; and runner manifest `runs/2026-07-15/986e7218-79a4-4a03-985c-5bb9c5831d4c/manifest.json` is legal, current-SHA-matching, and has `created / partial / official_written_partial` accepted by the semantic matrix.
- Directed Phase C regression: `python3 -m pytest -q tests/test_review_manifest.py` → `122 passed`.
- 2026-07-15 idempotent rerun with the same runtime and matching runner manifest → `review_already_exists`; it returned the existing canonical review ID and wrote no new review/index artifact.
- The six canonical facts SHA-256 values and all six runtime runner-manifest and review-manifest SHA-256 values were rechecked and are unchanged from the tables above.
- P1=0; P2=0. The original finding remains above as the discovery record. Final conclusion: ready to seal.
