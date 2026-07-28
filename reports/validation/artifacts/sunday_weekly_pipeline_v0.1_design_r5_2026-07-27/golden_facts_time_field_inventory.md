# 300274 2026-07-24 黄金 facts 时间字段清单

Sample SHA-256: `09b30acc84ae65715859101880ba9eb4ac1c5bf14afa27770323f0e806debff7`.

| JSON path | Raw value | Normalized kind | Cutoff role |
|---|---|---|---|
| `$.generated_at` | `2026-07-25T20:17:26Z` | provenance | excluded |
| `$.quote_verification.fetched_at` | `2026-07-25T20:17:25Z` | provenance | excluded |
| `$.quote_verification.source_date` | `2026-07-24` | daily_bar | market date |
| `$.run.fetched_at` | `2026-07-25T20:17:25Z` | provenance | excluded |
| `$.run.target_date` | `2026-07-24` | daily_bar | market date |
| `$.trade_date` | `2026-07-24` | daily_bar | market date |
| `$.volume_ratio.cross_check.source_date` | `2026-07-24` | daily_bar | market date |
| `$.volume_ratio.five_day_volume_check.fetched_at` | `2026-07-25T20:17:26Z` | provenance | excluded |
| `$.volume_ratio.five_day_volume_check.trade_dates[0..5]` | `2026-07-17,20,21,22,23,24` | daily_bar | market dates |
| `$.volume_ratio.snapshot_ohlc_check.fetched_at` | `2026-07-25T20:17:26Z` | provenance | excluded |
| `$.volume_ratio.snapshot_ohlc_check.source_date` | `2026-07-24` | daily_bar | market date |
| `$.volume_ratio.verification.fetched_at` | `2026-07-25T20:17:25Z` | provenance | excluded |
| `$.volume_ratio.verification.source_date` | `2026-07-24` | daily_bar | market date |

All `fetched_at` occurrences, all `source_date` occurrences, and all `volume_ratio.*.trade_dates[]` elements in the sealed sample are enumerated above.
