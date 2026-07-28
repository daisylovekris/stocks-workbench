# 时间证据标准化 r4

`source_kind` is an SWP internal normalized type, not an input-file field requirement. For `facts_pack_v0.2`, register only these paths:

| Registered path | normalized source_kind | accepted format | cutoff role |
|---|---|---|---|
| `generated_at`, `**.fetched_at` | provenance | RFC3339 offset/Z | excluded |
| `trade_date`, `run.target_date`, `**.source_date`, `volume_ratio.*.trade_dates[]` | daily_bar | `YYYY-MM-DD` | market date |
| explicit announcement/news/policy registry fields | announcement/news/policy | RFC3339 offset/Z | market timestamp |

An unregistered time-looking field, unknown schema version, or conflicting path meaning is `blocked_future_data:source_time_unverifiable`. Naive datetime and date-only external news are rejected. Free text is never machine time evidence. Normalization has no dependency on a literal `source_kind` key in source JSON.

Golden input `data/daily/300274_2026-07-24_facts.json` demonstrates the rule: `generated_at`/`fetched_at` are 2026-07-25 provenance and remain legal; `trade_date`/`source_date` are 2026-07-24 daily_bar evidence.
