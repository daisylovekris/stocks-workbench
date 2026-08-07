# Sungrow Daily Review Backfill 2026-07-27 to 2026-07-31 Validation

## Backfill context

| Field | Value |
|---|---|
| `symbol` | `300274` |
| `name` | 阳光电源 |
| `date_range` | `2026-07-27` → `2026-07-31` |
| `as_of_head` | `1ecfb2fd932230ac86bd890797c15fa7fa37b431` |
| `runtime_root` | repository-external |

2026-07-27 through 2026-07-30 reviews are bound to the authoritative Phase C
review manifests created from the exact new Phase B runs (`needs_manual_review`).
2026-07-31 is a human review of valid official facts with no current Phase C:
original provenance unavailable, Phase B authority missing, Phase C absent,
automation disposition `KEEP_DEFERRED`, automated SWP inclusion denied. Strict
time boundaries were enforced for every review: each only references
information available up to that trading day's close. Background gaps remain
TODO/null; no indices, sectors, disclosures, news, or policy causes were
fabricated. No cost recalculation was performed; the 07-30 buy at 104.79/100
shares and total position 400 shares were recorded as user human decisions
only, with overall cost marked as pending broker confirmation.

## Per-day record

### 2026-07-27

| Field | Value |
|---|---|
| `trade_date` | `2026-07-27` |
| `review_path` | `sungrow/reviews/sungrow_review_2026-07-27.md` |
| `review_size_bytes` | `5730` |
| `review_sha256` | `f48d5b5d1b3711d30461f2debc7c257576aab12f2367a6b5670687811c076dcf` |
| `facts_path` | `data/daily/300274_2026-07-27_facts.json` |
| `facts_sha256` | `b8c7b2b843b72ca10b3b6b23b13bc59d709c1fb2011886229a1dfd013939ad65` |
| `manifest_path` | `<runtime>/reviews/2026-07-27/rev_300274_2026-07-27_b8c7b2b843b72ca1/review_manifest.json` |
| `manifest_sha256` | `b1c09c0431f5c8b1967ca4c1471e50ebf35dc11ffe30dad17d08fac30f60c1bd` |
| `run_status` | `partial` |
| `review_state` | `needs_manual_review` |
| `future_date_reference_count` | `0` |
| `facts_value_mismatch_count` | `0` |
| `permission_overreach_count` | `0` |
| `trade_fact_mismatch_count` | `0` |

Market values: open=114.43, high=116.69, low=112.01, close=116.21, prev_close=113.42, pct_change≈+2.46%, amount=46.452244 亿, turnover=2.56%, volume_ratio=0.56. Position: 300 shares; no user-confirmed new transaction. Header facts SHA and manifest SHA match official bytes and authoritative Phase C bytes exactly.

### 2026-07-28

| Field | Value |
|---|---|
| `trade_date` | `2026-07-28` |
| `review_path` | `sungrow/reviews/sungrow_review_2026-07-28.md` |
| `review_size_bytes` | `5965` |
| `review_sha256` | `72147423eb9f1a24a879d182f7e4cd5fb886a4af325f7b40721259f8e7cdcf69` |
| `facts_path` | `data/daily/300274_2026-07-28_facts.json` |
| `facts_sha256` | `f9a875ddff0f1b94828406bd5ebca9ab6840163f708bbd7a127aebdc1de1cde4` |
| `manifest_path` | `<runtime>/reviews/2026-07-28/rev_300274_2026-07-28_f9a875ddff0f1b94/review_manifest.json` |
| `manifest_sha256` | `7a1d2255213cea4bff1cdd0361cc80d0158435ff660b5df2c0a2dad18ee03af3` |
| `run_status` | `partial` |
| `review_state` | `needs_manual_review` |
| `future_date_reference_count` | `0` |
| `facts_value_mismatch_count` | `0` |
| `permission_overreach_count` | `0` |
| `trade_fact_mismatch_count` | `0` |

Market values: open=115.72, high=115.77, low=110.24, close=112.08, prev_close=116.21, open_minus_prev_close=-0.49, opening_relation=low_open, pct_change≈-3.55%, amount=55.749262 亿, turnover=3.13%, volume_ratio=0.73. Position: 300 shares. prev_close=116.21 matches 2026-07-27 close. Opening relation corrected to low_open; review text now reads "低开 115.72" consistently.

### 2026-07-29

| Field | Value |
|---|---|
| `trade_date` | `2026-07-29` |
| `review_path` | `sungrow/reviews/sungrow_review_2026-07-29.md` |
| `review_size_bytes` | `6025` |
| `review_sha256` | `35afbbafabef5673b81559087452e5f8ea92aebd035c63136790464d87e25c96` |
| `facts_path` | `data/daily/300274_2026-07-29_facts.json` |
| `facts_sha256` | `6ad580d29365825f75edacca54c3e337b6493abdff7902b94e78b5cbc624f44d` |
| `manifest_path` | `<runtime>/reviews/2026-07-29/rev_300274_2026-07-29_6ad580d29365825f/review_manifest.json` |
| `manifest_sha256` | `afd149f248f5dfb4795ed26e8be7a2ba38f7ef02cec23910f099fccd54337c04` |
| `run_status` | `partial` |
| `review_state` | `needs_manual_review` |
| `future_date_reference_count` | `0` |
| `facts_value_mismatch_count` | `0` |
| `permission_overreach_count` | `0` |
| `trade_fact_mismatch_count` | `0` |

Market values: open=109.30, high=110.00, low=100.71, close=106.55, prev_close=112.08, pct_change≈-4.93%, amount=94.209094 亿, turnover=5.70%, volume_ratio=1.40. User trade fact: had multiple pending buy orders, all unfilled; no new position; closing position still 300 shares. "Pending orders" is not written as "already bought". prev_close=112.08 matches 2026-07-28 close.

### 2026-07-30

| Field | Value |
|---|---|
| `trade_date` | `2026-07-30` |
| `review_path` | `sungrow/reviews/sungrow_review_2026-07-30.md` |
| `review_size_bytes` | `6246` |
| `review_sha256` | `f9e5dd0294cedb93c3550803354ed4b1a19d409b1b43b19147daf9adbc6604f7` |
| `facts_path` | `data/daily/300274_2026-07-30_facts.json` |
| `facts_sha256` | `8484e42eeeeb12dc7f6b127f11eab3c8bf964bf64375d587dac39a2c37024d4b` |
| `manifest_path` | `<runtime>/reviews/2026-07-30/rev_300274_2026-07-30_8484e42eeeeb12dc/review_manifest.json` |
| `manifest_sha256` | `5b1f82307fa634febe2943b43328a6a008036c68a33df3f0a9643043ae4d39e2` |
| `run_status` | `partial` |
| `review_state` | `needs_manual_review` |
| `future_date_reference_count` | `0` |
| `facts_value_mismatch_count` | `0` |
| `permission_overreach_count` | `0` |
| `trade_fact_mismatch_count` | `0` |

Market values: open=104.74, high=106.70, low=102.11, close=103.71, prev_close=106.55, pct_change≈-2.67%, amount=54.899181 亿 (float noise `54.899181000000006` not copied into Markdown), turnover=3.32%, volume_ratio=0.80. User trade fact: bought 100 shares at 104.79; total position 400 shares after fill; close 103.71 is 1.08 below buy price; overall cost marked as pending broker confirmation; no cost recalculation from old 181 baseline. prev_close=106.55 matches 2026-07-29 close.

### 2026-07-31

| Field | Value |
|---|---|
| `trade_date` | `2026-07-31` |
| `review_path` | `sungrow/reviews/sungrow_review_2026-07-31.md` |
| `review_size_bytes` | `7958` |
| `review_sha256` | `d4d244978594d5a8f5525ef494cad06bdfedd74f8d103e5bbed695b45361a91f` |
| `facts_path` | `data/daily/300274_2026-07-31_facts.json` |
| `facts_sha256` | `196d2b24fcd4d600db0c7b55d367c229cf9132526576ad0970ab163d4a9a99cd` |
| `facts_valid` | `YES` |
| `original_provenance` | `unavailable` |
| `Phase_B_authority` | `missing` |
| `Phase_C` | `absent` |
| `automation_disposition` | `KEEP_DEFERRED` |
| `automated_SWP_inclusion` | `denied` |
| `fable_verdict` | `KEEP_DEFERRED` |
| `historical_locator_only` | 旧 Phase B run `<runtime>/runs/2026-07-31/b6a27a19-cc1c-4c2e-b600-aca7b575c864/manifest.json`、旧 Phase C `<runtime>/reviews/2026-07-31/rev_300274_2026-07-31_196d2b24fcd4d600/review_manifest.json`、旧 claimed SHA `3ecfd1c4328a2feb5f49072a4d4cf2265b75edb93648fcd60e7cae56ad6bceba`——locator-only，raw bytes absent / provenance unavailable |
| `future_date_reference_count` | `0` |
| `facts_value_mismatch_count` | `0` |
| `permission_overreach_count` | `0` |
| `trade_fact_mismatch_count` | `0` |

Human review of valid official facts: open=107.00, high=107.70, low=103.02, close=103.37, prev_close=103.71, pct_change≈-0.33%, amount=49.63731254 亿, turnover=2.97%, volume_ratio=0.82. Position: 400 shares, no further expansion; switched to short-term management. This review does not claim current Phase C authority: no current Phase C manifest SHA is recorded. Old Phase B / Phase C locators are locator-only (raw bytes absent). Fable verdict KEEP_DEFERRED; automated SWP inclusion denied. Next-session observation section only registers observation dimensions; no August market data or news used. prev_close=103.71 matches 2026-07-30 close.

07-31 Phase B authority missing 会阻断 2026-07-27～2026-07-31 整周自动 SWP
候选；禁止生成仅含 07-27～07-30 的四日自动周候选。

```text
DATE_2026_07_31_AUTOMATED_SWP_INCLUSION=DENIED
WEEK_2026_07_27_2026_07_31_AUTOMATED_SWP_CANDIDATE=BLOCKED
SWP_BLOCK_REASON=blocked_identity_conflict:phase_b_evidence_missing
FOUR_DAY_AUTOMATED_WEEKLY_CANDIDATE=PROHIBITED
```

## Cross-day verification

- **Title/date match**: each review title and filename date equals the trade date.
- **Facts SHA match**: every review header facts SHA equals the recomputed official bytes SHA.
- **Manifest SHA match (07-27 to 07-30)**: each of the four review header manifest SHAs equals the recomputed authoritative Phase C bytes SHA. 07-31 has no current Phase C, so manifest SHA match is not applicable.
- **Market values match**: OHLC, prev_close, pct_change, amount, turnover_rate, volume_ratio in each review match the corresponding official facts; 07-30 amount displayed as 54.899181 亿 without float noise.
- **Opening-vs-prev_close relation**: each review's opening description matches the recomputed open−prev_close sign:
  - 2026-07-27: high_open (open 114.43 > prev_close 113.42)
  - 2026-07-28: low_open (open 115.72 < prev_close 116.21, open_minus_prev_close=-0.49)
  - 2026-07-29: low_open (open 109.30 < prev_close 112.08)
  - 2026-07-30: low_open (open 104.74 < prev_close 106.55)
  - 2026-07-31: high_open (open 107.00 > prev_close 103.71)
  The four previously-incorrect 07-28 opening phrases (high-open wording contradicting the low-open open−prev_close sign) are absent from all three modified files.
- **prev_close chain**: 113.42 (07-24 close) → 07-27 prev_close 113.42 → 07-27 close 116.21 → 07-28 prev_close 116.21 → 07-28 close 112.08 → 07-29 prev_close 112.08 → 07-29 close 106.55 → 07-30 prev_close 106.55 → 07-30 close 103.71 → 07-31 prev_close 103.71. Chain intact.
- **Trade facts**: 07-29 no fill, position 300; 07-30 bought 104.79/100 shares, total 400; 07-31 total 400, no expansion. "Pending orders" not written as "bought".
- **Cost recalculation**: none; overall cost marked as pending broker confirmation; old 181 baseline not used to reverse-calculate new average; no fees or actual cost speculated.
- **Future data**: no review references any later trading day's market data.
- **Background fiction**: none; all four background fields remain TODO/null.
- **Permission overreach**: 07-27 to 07-30 Phase C downstream permissions are all `false`; 07-31 has no Phase C downstream permission object and no automatic downstream authorization; no trading action or Git authority granted.
- **Duplicate opening narrative**: the 07-28 `### 115.77 / 116.21` section previously contained repeated opening-narrative bullets; it is now consolidated into three non-redundant bullets. DUPLICATE_OPENING_NARRATIVE_COUNT=0.
- **Scope**: current cards, `stock_workbench_index.md`, `weekly/`, `config/a_share_trading_calendar_2026.json`, `rules/`, `tools/`, `tests/` were not modified. The five official facts files were not modified. Pre-existing unrelated dirty items remain in the working tree.

## Fixed output

```
DAILY_REVIEW_COUNT=5
PHASE_C_BOUND_REVIEW_COUNT=4
HUMAN_ONLY_FACTS_REVIEW_COUNT=1
ALL_FACTS_SHA_MATCH=YES
FOUR_DAY_MANIFEST_SHA_MATCH=YES
DATE_2026_07_31_PHASE_C=ABSENT
DATE_2026_07_31_AUTOMATION_DISPOSITION=KEEP_DEFERRED
ALL_MARKET_VALUES_MATCH=YES
PREV_CLOSE_CHAIN_MATCH=YES
OPEN_PREV_CLOSE_RELATION_MISMATCH_COUNT=0

FUTURE_DATE_REFERENCE_COUNT=0
FACTS_VALUE_MISMATCH_COUNT=0
PERMISSION_OVERREACH_COUNT=0
TRADE_FACT_MISMATCH_COUNT=0
COST_RECALCULATION_COUNT=0
DUPLICATE_NARRATIVE_COUNT=0

CURRENT_CARDS_MODIFIED=NO
INDEX_MODIFIED=NO
WEEKLY_MODIFIED=NO
CALENDAR_MODIFIED=NO

P1_COUNT=0
P2_COUNT=0
P3_COUNT=0

DAILY_REVIEW_BACKFILL_READY_FOR_REVIEW=YES
POST_COMMIT_MEMORY_REFRESH_REQUIRED=YES

INDEX_EMPTY=YES
STAGED=NO
COMMITTED=NO
PUSHED=NO
```
