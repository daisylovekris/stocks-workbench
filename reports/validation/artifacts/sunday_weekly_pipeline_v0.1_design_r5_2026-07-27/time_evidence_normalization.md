# 时间证据标准化 r5

`source_kind` is SWP-internal normalization. For `facts_pack_v0.2`: `generated_at` and `**.fetched_at` are provenance; `trade_date`, `run.target_date`, `**.source_date`, and `volume_ratio.*.trade_dates[]` are daily_bar. Announcement/news/policy require explicit registered structured RFC3339 offset/Z fields. Unknown schema, unregistered time field, semantic-path conflict, naive datetime, date-only external event, and free-text-only evidence are `blocked_future_data:source_time_unverifiable`.

The sealed golden sample and complete concrete inventory are `snapshots/golden/300274_2026-07-24_facts.json` and `golden_facts_time_field_inventory.md`.
