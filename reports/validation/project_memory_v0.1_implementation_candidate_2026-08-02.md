# Project Memory v0.1 Implementation Candidate Validation

## Scope and HEAD identity

This report validates the first worktree-only Project Memory v0.1 implementation candidate against the design frozen by closure commit `5e8c1a39dcc81697e3d46ff244162d64290e2b11`.

- `HEAD=5e8c1a39dcc81697e3d46ff244162d64290e2b11`
- `current_branch=workbench/mainline-2026-07`
- `validation_date=2026-08-02`
- `memory_file_count=13`
- `evidence_object_count=66`

No existing rule, code, test, business data, business document, frozen design artifact, closure artifact, or formal Fable review artifact was modified.

## Exact Memory file set and identity

| Path | Size bytes | SHA-256 |
|---|---:|---|
| `memory/README.md` | 2874 | `a69eb4de77084fc10d5f7a83d7f743fffc389105c28911bf5892c4f6ce3fb0e6` |
| `memory/agent_benchmark.md` | 10727 | `ce2bdb177f09c2400f917720b78f41c6afaac8bde1850d0d3e3f50622d3ba89e` |
| `memory/decisions/ADR-0001.md` | 1153 | `bd4fd73d73f83d7bf8278cf8da1265f0362731c80c7e4217ae19a6e06681db0d` |
| `memory/decisions/ADR-0002.md` | 1244 | `7378cfe32f123f54f1fa5522033d4066b7838652fa80a6d91a610620d057127b` |
| `memory/decisions/ADR-0003.md` | 1500 | `7469535b7bf65a7a480993d42c8f5cbb06df3a8baef7fdb64e725fefda5d592f` |
| `memory/decisions/ADR-0004.md` | 1499 | `32604df46b90ba3b17a8847cf5d092ecf3701d8f1b6fb0e75a82fac4aaf39839` |
| `memory/decisions/ADR-0005.md` | 1126 | `12f18e732d36d16d0ca5acee275e8a665b848e5695fbb1ca73bb9fa3a83a34c7` |
| `memory/decisions/ADR-0006.md` | 1511 | `de6128c0f92449e8a56e558f88d80c587fa4d9198b64636548d5cd5350b7b7c9` |
| `memory/decisions/ADR-0007.md` | 1440 | `aeb0662668fe1a058d735df56674391669a3244ef7a9dee6ef32fb8f181e9d26` |
| `memory/decisions/ADR-0008.md` | 1793 | `df681fda3fea3d368e7835db30a78964499a141df5882d1fab01ecb6f1a29154` |
| `memory/decisions/ADR-0009.md` | 1731 | `44b2313bd74e80f8c4b4041ce159e8290c96d582a6ae56eb851fa02650e2c97e` |
| `memory/phase_registry.md` | 13118 | `6ec5576800412e0a60214a4886e58b72e11dc7cd99384643f5dbc881b11dd982` |
| `memory/project_state.md` | 6846 | `c3c9ad62558d200971408d3583ab2700fc56c54d5058bb7ff8a2bd12501b252d` |

The set contains no extra file. In particular, it contains no `memory/manifest.json`, copied source inventory, or validator.

## Exact record sets

- Phase set: `A`, `B`, `C`, `semantic_noop`, `SWP`, `project_memory`, `D`.
- Agent set: `Luna`, `Terra`, `Sol`, `gpt-5.5 high`, `Pi Fable`, `Bare Fable`, `Kimi Code`, `GLM`, `MiMo`.
- ADR set: `ADR-0001` through `ADR-0009` with no gap or extra record.
- ADR statuses: 0001-0005 and 0007 remain `proposed`; 0006, 0008, and 0009 remain `accepted`.

The Project Memory phase has the required implementation-candidate state: frozen design, implementation in progress, implementation validation not started, design closure closed at `5e8c1a39dcc81697e3d46ff244162d64290e2b11`, no downstream permissions, and next action `implementation_validation`.

The Pi Fable primary record continues to represent only the frozen SWP observed run at low effort, `1.004 USD/run`, and `101 seconds`. The Project Memory r5 external review remains navigable through the existing project_memory Phase evidence, project_state design-closure reference, final closure report, and committed Fable raw review and run_meta. The failed CUN Pi diagnostic remains excluded diagnostics prose only.

## Schema, enum, and Markdown checks

- Every project-state field required by `file_schema_matrix.md` is present in the metadata table.
- Every Phase record contains all 22 required fields.
- Every primary Agent record contains all 27 required fields.
- No primary Agent record contains an undeclared schema or authority field.
- Every ADR contains all required fields and the 11 fixed sections.
- All Phase status, closure-scope, Agent record-type, evidence-disposition, ADR status, and ADR decision-basis values remain within the frozen enums.
- README has the six fixed sections; Phase has seven fixed record headings; all nine ADR files have the fixed section order.
- Every path in each Phase path array has matching evidence by exact path.

## Evidence validation

All 66 formal evidence objects contain exactly `path`, `snapshot_kind`, `snapshot_commit`, `raw_sha256`, and `role`.

For every object, validation confirmed:

- the path is repository-relative and exists in the current repository;
- `snapshot_kind=commit`;
- `snapshot_commit` is a real 40-character commit;
- `git show snapshot_commit:path` succeeds;
- SHA-256 of those exact bytes equals `raw_sha256`;
- the role is non-empty;
- no source ID, alias, worktree identity, absolute path, or future implementation commit substitutes for the full object.

The final Project Memory design closure report, closure manifest, r5 design manifest, Fable raw review, and Fable run metadata are all bound to the pre-existing design closure commit `5e8c1a39dcc81697e3d46ff244162d64290e2b11`.

P1/P2/P3 were recomputed from the committed Fable raw review and committed run metadata; both sources report `0/0/0`.

## Safety and authority checks

- No credential-like value, private key, access-key pattern, API-key pattern, or bearer token was found.
- No trading, Git, business-state, or review-verdict authority is granted.
- SWP `candidate_only` is treated as a restriction and not an authority grant.
- No 40-character commit reference points to a nonexistent or future commit.
- No file refers to its own future implementation commit.
- Chat synchronization, source reverse-writing, broad staging, automatic push, and general model ranking remain prohibited.

## Git and implementation boundary

- Git HEAD remained `5e8c1a39dcc81697e3d46ff244162d64290e2b11`.
- Git index remained empty.
- No commit or push was performed.
- No production validator was created or implemented.
- Existing unrelated dirty paths remain outside the candidate.

## Git visibility diagnosis

- Candidate paths are visible to Git status and are untracked rather than ignored.
- No matching repository or global ignore rule applies to `memory/README.md`, `memory/agent_benchmark.md`, or this validation report.
- None of those paths is currently tracked; a future commit would not require force-add solely because of ignore rules.

## Fixed results

```text
EXPECTED_MEMORY_FILE_SET_MATCH=YES
EXPECTED_PHASE_SET_MATCH=YES
EXPECTED_AGENT_SET_MATCH=YES
EXPECTED_ADR_SET_MATCH=YES
ALL_REQUIRED_FIELDS_PRESENT=YES
ALL_PRIMARY_AGENT_FIELDS_PRESENT=YES
UNDECLARED_AGENT_SCHEMA_FIELD_COUNT=0
ALL_ROUTING_EVIDENCE_NONEMPTY=YES
ALL_ADMITTED_RUN_EVIDENCE_NONEMPTY=YES
ALL_EVIDENCE_OBJECTS_COMPLETE=YES
ALL_SOURCE_IDENTITIES_MATCH=YES
SYMBOLIC_EVIDENCE_COUNT=0
ABSOLUTE_PATH_COUNT=0
SECRET_FINDING_COUNT=0
AUTHORITY_GRANT_COUNT=0
FUTURE_COMMIT_REFERENCE_COUNT=0
MEMORY_MANIFEST_CREATED=NO
PRODUCTION_VALIDATOR_CREATED=NO
STAGED=NO
COMMITTED=NO
PUSHED=NO

GIT_STATUS_CANDIDATE_VISIBLE=YES
MEMORY_PATH_IGNORED=NO
VALIDATION_REPORT_IGNORED=NO
IGNORE_SCOPE=none
FORCE_ADD_REQUIRED_FOR_FUTURE_COMMIT=NO
INDEX_EMPTY=YES

P1_COUNT=0
P2_COUNT=0
P3_COUNT=0

IMPLEMENTATION_CANDIDATE_READY_FOR_REVIEW=YES
```
