# Sunday Weekly input-set contract v0.1

Canonical path: `rules/sunday_weekly_input_set_v0.1.schema.json`. Read its raw UTF-8 bytes with `safe_file_read`; bytes, SHA-256 and parsed JSON must come from one FD at the initial snapshot and final commit. Its SHA must equal semantic config `input_set_schema_raw_sha256`, otherwise `blocked_identity_conflict:input_set_schema_identity_invalid`, all permissions false and retryable.

The input-set object has exactly this schema field set. Canonical bytes are UTF-8 JSON with `sort_keys=true`, `separators=(',', ':')`, no BOM, no trailing LF and no whitespace. `calendar_identities` sort by `calendar_year`; `daily_inputs` sort by `trade_date`. `input_set_sha256=sha256(canonical bytes)`.

Only these semantic identities are included: calendar year/raw SHA; semantic-config raw SHA; and, per trade date, facts raw SHA, true `sungrow/reviews/sungrow_review_YYYY-MM-DD.md` raw SHA, Phase B manifest raw SHA and authoritative Phase C manifest raw SHA. Bundle-relative evidence paths, snapshot paths, Phase C index bytes, diagnostic data, candidate bytes and validator output are prohibited from the input set. Phase C index path/entry remains audit evidence in the runtime manifest and is re-resolved during final validation.
