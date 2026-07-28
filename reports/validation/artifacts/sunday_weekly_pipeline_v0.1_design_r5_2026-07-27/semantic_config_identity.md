# SWP semantic config identity r5

`swp_semantic_config_sha256=sha256(UTF-8 canonical JSON)` where the JSON has these mandatory keys and values:

- `candidate_schema_version`
- `partial_whitelist`: exactly `market_indices`, `sector_context`, `disclosure_status`, `news_policy_context`
- `phase_c_accepted_states`: exactly `needs_manual_review`, `ready_for_human_review`
- `time_evidence_path_registry`: the facts_pack_v0.2 registry in `time_evidence_normalization.md`
- `timezone_cutoff_contract`: `Asia/Shanghai`; last-trading-day close; daily_bar date versus external RFC3339 offset/Z; provenance excluded

The SHA is part of input_set, completion manifest, and live completion revalidation. Altering any member changes input_set_sha256 and cannot be SWP no-op.
