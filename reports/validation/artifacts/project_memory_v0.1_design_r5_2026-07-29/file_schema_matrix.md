# Formal schema matrix

## `project_state`

Required fields: `schema_version`, `as_of_commit`, `as_of_date`, `current_branch`, `current_milestone`, `work_status`, `completed_scopes`, `completed_closures`, `active_work`, `queued_work`, `deferred_work`, `blockers`, `known_dirty_exclusions`, and `source_references`.

## `phase_registry`

Required fields: `phase_id`, `name`, `scope`, `work_status`, `completed_scopes`, `design_status`, `implementation_status`, `validation_status`, `closure_status`, `closure_scope`, `relationship`, `superseded_by`, `rule_paths`, `implementation_paths`, `test_paths`, `validation_paths`, `sealing_commit`, `dependencies`, `downstream_permissions`, `deferred_items`, `next_allowed_action`, and `evidence`.

Every path in the four path arrays requires exactly matching evidence by `path`. The sole allowed unsealed exception is `project_memory` while `work_status=in_progress`, for which `sealing_commit=null`, all four path arrays are empty, and `evidence=[]`.

## `agent_benchmark`

Required fields: `record_type`, `agent_or_model`, `provider_backend`, `task_class`, `actual_model_evidence`, `reasoning_effort`, `observed_result`, `evidence_scope`, `sample_count`, `model_identity_confidence`, `cost`, `cost_currency`, `cost_scope`, `latency`, `limitations`, `adjudication_path`, `evidence_disposition`, `benchmark_eligible`, `adr_eligible`, `strengths`, `weaknesses`, `suitable_role`, `unsuitable_role`, `confidence`, `last_verified_date`, and `evidence`.

`record_type` is exactly `routing_policy | observed_run | pending_observation`. Every admitted `observed_run` has non-empty evidence. `routing_policy` must cite the routing follow-up. `pending_observation` may use `evidence=[]`.

## ADR

Required fields: `ID`, `title`, `status`, `decision_basis`, `scope`, `date`, `decision`, `context`, `alternatives`, `consequences`, `authority_boundaries`, `evidence`, `supersedes`, and `superseded_by`.

`status` is exactly `proposed | accepted | superseded | rejected`. `decision_basis` is exactly `owner_decision | documents_existing_authority | pending_owner_decision`. Symbolic evidence is forbidden.

## Source inventory and evidence

Every source-inventory entry requires `id`, `path`, `authority_class`, `category`, `role`, `used_by`, `snapshot_kind`, `snapshot_commit`, `sealing_commit`, `path_raw_sha256`, `exists_at_snapshot`, and `historical_or_current`.

Every formal evidence object is exactly commit-bound `{path, snapshot_kind, snapshot_commit, raw_sha256, role}`. `snapshot_kind` is `commit`; `snapshot_commit` is 40 lowercase hexadecimal characters; `raw_sha256` is 64 lowercase hexadecimal characters. Formal evidence contains repository-relative paths only and must match a source-inventory `path` and `path_raw_sha256`.
