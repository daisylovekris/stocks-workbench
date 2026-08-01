# Validation plan

The production validator is deferred. When implemented later, it is read-only and fail-closed: it writes no project file, changes no Git state, performs no network call, and grants no downstream permission. This r5 round uses ad hoc deterministic content checks only and creates no validator.

## Snapshot modes

| mode | bytes read | identity rule | prohibited side effect |
|---|---|---|---|
| `--worktree` | Current working-tree bytes for the explicit candidate path set | Evidence sources still resolve against each record’s declared commit snapshot; candidate Markdown/JSON is read from the worktree | No staging, formatting, report generation, or source rewrite |
| `--index` | Git index blobs for the exact staged candidate path set | The staged blob set must equal the intended package membership and all source identities remain commit-bound | No mutation of index or worktree |
| `--commit <sha>` | The specified Git tree only | The commit must exist, every required member must exist in that tree, and every source/evidence identity must resolve at its declared snapshot | No checkout, branch movement, tag, commit, or push |

Required lifecycle: worktree validation → precise staging → index validation → independent review → scoped commit → commit validation. Success in one mode never substitutes for the next mode.

## Identity checks

- `source_inventory.json` parses as JSON; declared and actual counts match; IDs and paths are unique.
- Every source has all required fields: `id`, `path`, `authority_class`, `category`, `role`, `used_by`, `snapshot_kind`, `snapshot_commit`, `sealing_commit`, `path_raw_sha256`, `exists_at_snapshot`, and `historical_or_current`.
- Every source path is repository-relative, normalized, and free of traversal.
- `snapshot_kind` is exactly `commit`; each snapshot commit is 40 lowercase hexadecimal characters and resolves to a commit.
- Every declared source exists or does not exist at the snapshot exactly as `exists_at_snapshot` states.
- `path_raw_sha256` is 64 lowercase hexadecimal characters and matches the raw bytes at `snapshot_commit:path`.
- A non-null sealing commit is 40 lowercase hexadecimal characters and resolves; it is separate from the source snapshot identity.
- Every formal evidence object has exactly `path`, `snapshot_kind`, `snapshot_commit`, `raw_sha256`, and `role`; its path and raw hash match one source-inventory entry.
- Path-only, source-ID-only, worktree-only, summary-only, UI-only, and chat-only evidence is rejected.
- A missing path, malformed identity, hash mismatch, or unresolved commit fails closed.

## Exact-set and schema checks

- Phase IDs equal exactly `A`, `B`, `C`, `semantic_noop`, `SWP`, `project_memory`, and `D`.
- Agent names equal exactly `Luna`, `Terra`, `Sol`, `gpt-5.5 high`, `Pi Fable`, `Bare Fable`, `Kimi Code`, `GLM`, and `MiMo`.
- ADR IDs equal exactly `ADR-0001` through `ADR-0009`.
- Every phase, Agent, ADR, and project-state record contains every field declared in `file_schema_matrix.md`; unknown extra authority fields are rejected.
- Every path in a phase rule, implementation, test, or validation array has a matching full evidence object.
- `project_memory` may remain `work_status=in_progress`, `sealing_commit=null`, with empty path arrays and `evidence=[]`.
- Every routing-policy record has routing-follow-up evidence.
- Every admitted observed run has non-empty evidence; GLM and MiMo may remain evidence-empty only as `pending_observation`.
- Failed CUN Pi appears only in `excluded_diagnostic_notes.md`, never in the formal Agent or ADR sets.
- Symbolic evidence phrases or aliases are rejected.

## Enumeration and relationship checks

- `work_status`, all four phase-status dimensions, `completed_scopes`, `closure_scope`, `memory_evidence_status`, and `evidence_disposition` use only `status_contract.md` values.
- `record_type` is exactly `routing_policy`, `observed_run`, or `pending_observation`.
- ADR `status` and `decision_basis` use only the values declared in `file_schema_matrix.md`.
- `implemented` requires implementation paths and evidence; `validated` requires validation paths and evidence; `closed` or `frozen_design` requires the applicable pre-existing sealing commit.
- Planned, deferred, pending, and in-progress records are never rendered as completed.
- Phase B extends Phase A and does not silently supersede it.
- Phase D remains a reservation/deferred item, not an implemented phase.
- SWP remains design-only and candidate-only; no implementation is inferred.
- Supersession requires explicit `supersedes` or `superseded_by` linkage; date order alone is insufficient.

## Conflict and authority checks

- `conflict_resolution_matrix.md` contains exactly the 15 named r4 scenarios and all eight columns.
- Each conflict row uses one allowed `memory_evidence_status`, has required evidence, and preserves the allowed/forbidden wording boundary.
- Canonical official facts remain primary over summaries, reviews, weekly notes, cards, or indexes.
- Cross-class differences remain separate; same-scope conflicts require adjudication.
- Routing policy is not a benchmark, and one admitted run is not a general ranking.
- `downstream_permissions` contains no trading, buy/sell, position, Git, review-verdict, business-state, or autonomous-execution grant. `candidate_only` is a restriction, not a grant.
- Memory does not authorize staging, commit, push, trading, current-card changes, official-facts changes, index changes, weekly conclusions, or review outcomes.
- No file contains its own future commit identity.

## Sensitive-information and path checks

- No absolute local path, home-directory path, local file URI, traversal component, or external runtime path appears in a formal seed.
- No secret, API key, token, cookie, password, private key, authorization header, session credential, or `.env` value is present.
- High-entropy findings are reviewed in context; known 40-hex commit IDs and 64-hex SHA-256 values are permitted identities.
- `.DS_Store`, editor swap files, caches, generated credentials, and unrelated dirty files are absent from the candidate membership.

## Markdown checks

- Required H1/H2 headings exist and heading order is valid.
- Fenced code blocks are balanced and declared YAML/JSON blocks parse.
- Tables have consistent column counts, valid separator rows, and no broken multiline cells.
- Repository links and referenced relative paths are normalized; dangling links fail.
- Duplicate ADR IDs, duplicate phase/Agent records, duplicate source IDs, and duplicate inventory paths fail.
- Prohibited symbolic evidence wording and accidental placeholders fail.

## Package-member checks

- The candidate contains the main r5 report plus the existing 17 r5 artifact files, with no added `memory/`, validator, production code, temporary file, or unrelated source.
- Every intended member exists in the selected mode; no unexpected deletion, rename, duplicate version, or extra member is accepted.
- The main report status agrees with `design_manifest.json`, seed sets, and the recorded content-validation results.
- `design_manifest.json` remains excluded from `sealed_files` to avoid self-reference.
- r5 package sealing identity has been calculated; the manifest records the sealed member identities and package SHA.
- focused review is the next allowed action. Staging, commit, and push remain outside this validation plan.
