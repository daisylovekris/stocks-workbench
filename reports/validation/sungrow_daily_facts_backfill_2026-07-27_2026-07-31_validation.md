# Sungrow (300274) Daily Facts Backfill 2026-07-27 to 2026-07-31 Validation

## Backfill context

| Field | Value |
|---|---|
| `symbol` | `300274` |
| `name` | 阳光电源 |
| `date_range` | `2026-07-27` → `2026-07-31` |
| `mode` | `historical_backfill` |
| `reason` | `User-authorized overdue facts backfill for the 2026-07-27 through 2026-07-31 review chain` |
| `as_of_head` | `1ecfb2fd932230ac86bd890797c15fa7fa37b431` |
| `runtime_root` | repository-external |

Current true state: all five official facts files are valid. 2026-07-27 through
2026-07-30 each formed a legitimate Phase B `semantic_noop`
(`official_unchanged`) from an explicit `--write-official` run, and each has a
Phase C `needs_manual_review` review manifest created from that exact Phase B
run. 2026-07-31 official facts are valid, but the original same-day provenance
raw bytes are unavailable, no Phase B authority exists, Phase C was not
generated, and automated SWP inclusion is denied (`KEEP_DEFERRED`).

## Per-day record

### 2026-07-27

| Field | Value |
|---|---|
| `trade_date` | `2026-07-27` |
| `official_path` | `data/daily/300274_2026-07-27_facts.json` |
| `official_size_bytes` | `4429` |
| `official_sha256` | `b8c7b2b843b72ca10b3b6b23b13bc59d709c1fb2011886229a1dfd013939ad65` |
| `Phase_B_outcome` | `official_unchanged` |
| `write_action` | `semantic_noop` |
| `reason_code` | `official_semantically_identical` |
| `official_changed` | `false` |
| `comparison_mode` | `method_profile_timestamp_paths_v3` |
| `profile_version` | `v0.3` |
| `profile_sha256` | `11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1` |
| `Phase_B_run_id` | `9e6a1be0-9b45-45b4-898a-58325fc3ee99` |
| `Phase_B_manifest_path` | `<runtime>/runs/2026-07-27/9e6a1be0-9b45-45b4-898a-58325fc3ee99/manifest.json` |
| `Phase_B_manifest_sha256` | `5e5d3688f924a3becfa3289d5c88e2920c598b48406b1ba86da866187cb94120` |
| `Phase_C_review_id` | `rev_300274_2026-07-27_b8c7b2b843b72ca1` |
| `Phase_C_review_state` | `needs_manual_review` |
| `Phase_C_manifest_path` | `<runtime>/reviews/2026-07-27/rev_300274_2026-07-27_b8c7b2b843b72ca1/review_manifest.json` |
| `Phase_C_manifest_sha256` | `b1c09c0431f5c8b1967ca4c1471e50ebf35dc11ffe30dad17d08fac30f60c1bd` |
| `unresolved_fields` | `[disclosure_status, market_indices, news_policy_context, sector_context]` |
| `required_metric_failure_count` | `0` |
| `future_data_failure_count` | `0` |
| `downstream_true_permission_count` | `0` |

Required metrics: open=114.43, high=116.69, low=112.01, close=116.21, prev_close=113.42, pct_change=2.459883618409453, amount=46.452244, turnover_rate=2.56, volume_ratio=0.56. All finite numeric; high≥open/close/low; low≤open/close/high.

### 2026-07-28

| Field | Value |
|---|---|
| `trade_date` | `2026-07-28` |
| `official_path` | `data/daily/300274_2026-07-28_facts.json` |
| `official_size_bytes` | `4430` |
| `official_sha256` | `f9a875ddff0f1b94828406bd5ebca9ab6840163f708bbd7a127aebdc1de1cde4` |
| `Phase_B_outcome` | `official_unchanged` |
| `write_action` | `semantic_noop` |
| `reason_code` | `official_semantically_identical` |
| `official_changed` | `false` |
| `comparison_mode` | `method_profile_timestamp_paths_v3` |
| `profile_version` | `v0.3` |
| `profile_sha256` | `11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1` |
| `Phase_B_run_id` | `a3cd9431-41b3-4df0-9d3b-52bb1017b3b5` |
| `Phase_B_manifest_path` | `<runtime>/runs/2026-07-28/a3cd9431-41b3-4df0-9d3b-52bb1017b3b5/manifest.json` |
| `Phase_B_manifest_sha256` | `42ace333952e08748729c99fb5230224fe59ff2dd98b548f43305f4fc46f3cc0` |
| `Phase_C_review_id` | `rev_300274_2026-07-28_f9a875ddff0f1b94` |
| `Phase_C_review_state` | `needs_manual_review` |
| `Phase_C_manifest_path` | `<runtime>/reviews/2026-07-28/rev_300274_2026-07-28_f9a875ddff0f1b94/review_manifest.json` |
| `Phase_C_manifest_sha256` | `7a1d2255213cea4bff1cdd0361cc80d0158435ff660b5df2c0a2dad18ee03af3` |
| `unresolved_fields` | `[disclosure_status, market_indices, news_policy_context, sector_context]` |
| `required_metric_failure_count` | `0` |
| `future_data_failure_count` | `0` |
| `downstream_true_permission_count` | `0` |

Required metrics: open=115.72, high=115.77, low=110.24, close=112.08, prev_close=116.21, pct_change=-3.553911023147749, amount=55.749262, turnover_rate=3.13, volume_ratio=0.73. prev_close=116.21 matches 2026-07-27 close.

### 2026-07-29

| Field | Value |
|---|---|
| `trade_date` | `2026-07-29` |
| `official_path` | `data/daily/300274_2026-07-29_facts.json` |
| `official_size_bytes` | `4420` |
| `official_sha256` | `6ad580d29365825f75edacca54c3e337b6493abdff7902b94e78b5cbc624f44d` |
| `Phase_B_outcome` | `official_unchanged` |
| `write_action` | `semantic_noop` |
| `reason_code` | `official_semantically_identical` |
| `official_changed` | `false` |
| `comparison_mode` | `method_profile_timestamp_paths_v3` |
| `profile_version` | `v0.3` |
| `profile_sha256` | `11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1` |
| `Phase_B_run_id` | `3ebef276-c3c7-4de7-af74-fb9b880c8fc8` |
| `Phase_B_manifest_path` | `<runtime>/runs/2026-07-29/3ebef276-c3c7-4de7-af74-fb9b880c8fc8/manifest.json` |
| `Phase_B_manifest_sha256` | `78da574ea5df0ced5745a589e2c8eabf58398c56643eb9ce0242a244846271e0` |
| `Phase_C_review_id` | `rev_300274_2026-07-29_6ad580d29365825f` |
| `Phase_C_review_state` | `needs_manual_review` |
| `Phase_C_manifest_path` | `<runtime>/reviews/2026-07-29/rev_300274_2026-07-29_6ad580d29365825f/review_manifest.json` |
| `Phase_C_manifest_sha256` | `afd149f248f5dfb4795ed26e8be7a2ba38f7ef02cec23910f099fccd54337c04` |
| `unresolved_fields` | `[disclosure_status, market_indices, news_policy_context, sector_context]` |
| `required_metric_failure_count` | `0` |
| `future_data_failure_count` | `0` |
| `downstream_true_permission_count` | `0` |

Required metrics: open=109.3, high=110.0, low=100.71, close=106.55, prev_close=112.08, pct_change=-4.9339757316202775, amount=94.209094, turnover_rate=5.7, volume_ratio=1.4. prev_close=112.08 matches 2026-07-28 close.

### 2026-07-30

| Field | Value |
|---|---|
| `trade_date` | `2026-07-30` |
| `official_path` | `data/daily/300274_2026-07-30_facts.json` |
| `official_size_bytes` | `4429` |
| `official_sha256` | `8484e42eeeeb12dc7f6b127f11eab3c8bf964bf64375d587dac39a2c37024d4b` |
| `Phase_B_outcome` | `official_unchanged` |
| `write_action` | `semantic_noop` |
| `reason_code` | `official_semantically_identical` |
| `official_changed` | `false` |
| `comparison_mode` | `method_profile_timestamp_paths_v3` |
| `profile_version` | `v0.3` |
| `profile_sha256` | `11bb039d16e91f8d799ae37fadb25b23505eee6919747b18b829fef146e2e4c1` |
| `Phase_B_run_id` | `c4f43408-5154-4f10-a96e-3841a1ef3d89` |
| `Phase_B_manifest_path` | `<runtime>/runs/2026-07-30/c4f43408-5154-4f10-a96e-3841a1ef3d89/manifest.json` |
| `Phase_B_manifest_sha256` | `deb589dd0f144b78f28a75c7c20de67c07b6ac5df11e1db143f491f23b84a9d5` |
| `Phase_C_review_id` | `rev_300274_2026-07-30_8484e42eeeeb12dc` |
| `Phase_C_review_state` | `needs_manual_review` |
| `Phase_C_manifest_path` | `<runtime>/reviews/2026-07-30/rev_300274_2026-07-30_8484e42eeeeb12dc/review_manifest.json` |
| `Phase_C_manifest_sha256` | `5b1f82307fa634febe2943b43328a6a008036c68a33df3f0a9643043ae4d39e2` |
| `unresolved_fields` | `[disclosure_status, market_indices, news_policy_context, sector_context]` |
| `required_metric_failure_count` | `0` |
| `future_data_failure_count` | `0` |
| `downstream_true_permission_count` | `0` |

Required metrics: open=104.74, high=106.7, low=102.11, close=103.71, prev_close=106.55, pct_change=-2.6654152979821766, amount=54.899181000000006, turnover_rate=3.32, volume_ratio=0.8. prev_close=106.55 matches 2026-07-29 close.

### 2026-07-31

| Field | Value |
|---|---|
| `trade_date` | `2026-07-31` |
| `official_path` | `data/daily/300274_2026-07-31_facts.json` |
| `official_size_bytes` | `4641` |
| `official_sha256` | `196d2b24fcd4d600db0c7b55d367c229cf9132526576ad0970ab163d4a9a99cd` |
| `official_facts_valid` | `YES` |
| `current_conflict_run_path` | `<runtime>/runs/2026-07-31/54681ca9-3c8b-46a2-8fdb-1ef487d71b9d/manifest.json` |
| `current_conflict_manifest_sha256` | `5fa5df4b8488c7486ba1820fb5e2fc49ed0338f4f91a1e24a39664919b4ebeb9` |
| `current_replay_method` | `historical_five_day_volume_cross_check` |
| `official_method` | `same_day_snapshot_plus_sohu_five_day_cross_check` |
| `cross_method_equivalence` | `rejected` |
| `Phase_B_authority` | `missing` |
| `Phase_C` | `absent` |
| `automation_disposition` | `KEEP_DEFERRED` |
| `automated_SWP_inclusion` | `denied` |
| `historical_locator_only` | 旧 Phase B run `<runtime>/runs/2026-07-31/b6a27a19-cc1c-4c2e-b600-aca7b575c864/manifest.json`、旧 Phase C `<runtime>/reviews/2026-07-31/rev_300274_2026-07-31_196d2b24fcd4d600/review_manifest.json`、旧 claimed SHA `3ecfd1c4328a2feb5f49072a4d4cf2265b75edb93648fcd60e7cae56ad6bceba`——均为 locator-only，raw bytes absent / provenance unavailable |
| `unresolved_fields` | `[disclosure_status, market_indices, news_policy_context, sector_context]` |
| `required_metric_failure_count` | `0` |
| `future_data_failure_count` | `0` |
| `downstream_true_permission_count` | `0` |

Required metrics: open=107.0, high=107.7, low=103.02, close=103.37, prev_close=103.71, pct_change=-0.32783723845336565, amount=49.63731254, turnover_rate=2.97, volume_ratio=0.82. prev_close=103.71 matches 2026-07-30 close.

## SWP 阻断（整周）

07-31 Phase B authority missing 会阻断 2026-07-27～2026-07-31 整周自动 SWP
候选；禁止生成仅含 07-27～07-30 的四日自动周候选。

```text
DATE_2026_07_31_AUTOMATED_SWP_INCLUSION=DENIED
WEEK_2026_07_27_2026_07_31_AUTOMATED_SWP_CANDIDATE=BLOCKED
SWP_BLOCK_REASON=blocked_identity_conflict:phase_b_evidence_missing
FOUR_DAY_AUTOMATED_WEEKLY_CANDIDATE=PROHIBITED
```

## Cross-day verification

- **Prev-close chain**: 2026-07-27 close 116.21 → 2026-07-28 prev_close 116.21; 2026-07-28 close 112.08 → 2026-07-29 prev_close 112.08; 2026-07-29 close 106.55 → 2026-07-30 prev_close 106.55; 2026-07-30 close 103.71 → 2026-07-31 prev_close 103.71. Chain intact.
- **Schema/symbol/trade_date**: all five facts carry `schema_version=facts_pack_v0.2`, `symbol=300274`, and a `trade_date` equal to the target day.
- **Required metric validity**: all `open/high/low/close/prev_close/pct_change/amount/turnover_rate/volume_ratio` fields are finite numbers; no `bool`, `NaN`, `Infinity`, or `null` appears in any required market field. `high ≥ open/close/low` and `low ≤ open/close/high` hold for every day.
- **Source timestamp**: `quote_verification.source_date` and `volume_ratio.cross_check.source_date` equal the trade date for every day; no future trading-day data was used to explain an earlier date.
- **Background fields**: `market_indices`, `sector_context`, `disclosure_status`, `news_policy_context` remain `null`/TODO as allowed; gaps were not inferred as bullish or bearish.
- **Phase B (07-27 to 07-30)**: each day formed `write_action=semantic_noop`, `outcome=official_unchanged`, `reason_code=official_semantically_identical`, `official_changed=false`, `comparison_mode=method_profile_timestamp_paths_v3`, `profile_version=v0.3`, `profile_sha256=11bb039d…`; official bytes unchanged on every day.
- **Phase C (07-27 to 07-30)**: four review manifests exist; each manifest's `official_sha256` matches the recomputed facts SHA exactly; `review_state=needs_manual_review`; all six `downstream_permissions` flags are `false`.
- **07-31**: official facts valid; original same-day provenance raw bytes unavailable; current replay (`historical_five_day_volume_cross_check`) differs from official method (`same_day_snapshot_plus_sohu_five_day_cross_check`) and is blocked by v3 (`conflict_blocked`); Phase B authority missing; Phase C absent; automation disposition `KEEP_DEFERRED`; automated SWP inclusion denied. Facts remain valid without automation authority.

## Boundary

This report only records state; the five official facts files were not modified. Runtime evidence outside the repository exists only for 07-27 to 07-30 (Phase B semantic_noop manifests + Phase C review manifests); 07-31 has only a conflict run as current runtime object and no Phase C. No card set, `stock_workbench_index.md`, weekly, or trade calendar was modified. The official facts were not staged, committed, or pushed.

## Fixed summary

```
TRADE_DATE_COUNT=5
OFFICIAL_FACTS_COUNT=5
PHASE_B_AUTHORITY_COUNT=4
PHASE_C_MANIFEST_COUNT=4
DEFERRED_DATE_COUNT=1
FACTS_VALID_WITHOUT_AUTOMATION_AUTHORITY_COUNT=1
DATE_2026_07_31_FACTS_VALID=YES
DATE_2026_07_31_PHASE_B_AUTHORITY=MISSING
DATE_2026_07_31_PHASE_C=ABSENT
DATE_2026_07_31_AUTOMATED_SWP=DENIED
ALL_DATE_IDENTITIES_MATCH=YES
ALL_REQUIRED_METRICS_VALID=YES
PREV_CLOSE_CHAIN_MATCH=YES
FUTURE_DATA_FAILURE_COUNT=0
DOWNSTREAM_TRUE_PERMISSION_COUNT=0
DAILY_REVIEW_CREATED_BY_FACTS_BACKFILL=NO
CURRENT_DAILY_REVIEW_COUNT=5
CURRENT_CARDS_MODIFIED=NO
INDEX_MODIFIED=NO
WEEKLY_CREATED=NO

P1_COUNT=0
P2_COUNT=0
P3_COUNT=0

FACTS_BACKFILL_READY_FOR_REVIEW=YES
POST_COMMIT_MEMORY_REFRESH_REQUIRED=YES

INDEX_EMPTY=YES
STAGED=NO
COMMITTED=NO
PUSHED=NO
```
