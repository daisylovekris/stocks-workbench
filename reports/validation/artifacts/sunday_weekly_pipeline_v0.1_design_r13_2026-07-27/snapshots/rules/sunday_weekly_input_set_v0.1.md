# Sunday Weekly input-set contract v0.1

Canonical schema path: rules/sunday_weekly_input_set_v0.1.schema.json. Canonical contract path: rules/sunday_weekly_input_set_v0.1.md. Both are identity-bearing raw UTF-8 files. At initial snapshot, final commit, valid matching completion/no-op, and orphan recovery, safe_file_read must derive each bytes/SHA/parse from one FD and compare schema SHA with input_set_schema_raw_sha256 and contract SHA with input_set_contract_raw_sha256 in semantic config. Schema drift blocks with blocked_identity_conflict:input_set_schema_identity_invalid; contract drift blocks with blocked_identity_conflict:input_set_contract_identity_invalid. Permissions are all false and retryable.

The input-set object has exactly the schema fields. Canonical bytes are UTF-8 JSON with sort_keys=true and separators=(',', ':'); no BOM, trailing LF or whitespace. calendar_identities sort by calendar_year and daily_inputs by trade_date. input_set_sha256 is SHA-256 of canonical bytes.

Only semantic identities are included: calendar year/raw SHA; semantic-config raw SHA; and, per trade date, facts raw SHA, true Daily Review raw SHA, Phase B manifest raw SHA and authoritative Phase C manifest raw SHA. The true Daily Review resolver is semantic-config daily_review_resolvers[symbol], then the registered template is formatted only with validated trade_date. No directory may be guessed; an unregistered symbol blocks with blocked_identity_conflict:unsupported_symbol.

Bundle-relative evidence paths, snapshot paths, Phase C index bytes, diagnostics, candidate bytes and validator output are prohibited from the input set. Phase C index path/entry is runtime-manifest audit evidence and is re-resolved at final validation. Recursive unresolved_fields values reject a bare JSON number with blocked_identity_conflict:unresolved_value_encoding_invalid; no implicit string conversion is allowed.

If the validated calendar window has zero trading days, return no_candidate_for_window:no_trading_days, all permissions false, write only diagnostic evidence, and create neither candidate nor completion index.
