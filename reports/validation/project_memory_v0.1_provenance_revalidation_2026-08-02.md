# Project Memory v0.1 Provenance Revalidation Candidate

## Scope

This candidate revalidates the Project Memory v0.1 implementation commit `e1723c26efb76bee2aa2b879233a738f4e7e2323` and scoped closure commit `844d8b541d7fd3165ce9e9a1725f207e1764da51`. It is a read-only provenance review. It grants no staging, commit, push, trading, review-verdict, or business-state authority.

## Historical contamination finding

The two historical raw review outputs remain byte-for-byte unchanged. Each contains one platform-generated memory citation envelope, one `MEMORY.md:` reference, and two embedded rollout IDs:

| Historical raw | Size bytes | SHA-256 | Citation blocks | `MEMORY.md:` references | Embedded rollout IDs |
|---|---:|---|---:|---:|---:|
| `reports/validation/artifacts/project_memory_v0.1_implementation_independent_review_2026-08-02/gpt55_high_raw_output.md` | 1358 | `9b7167727a4d4b4732f09e890d0ca1e80bb74bb678c3f059f08ea32a24c1d6b7` | 1 | 1 | 2 |
| `reports/validation/artifacts/project_memory_v0.1_implementation_closure_delta_review_2026-08-02/gpt55_high_raw_output.md` | 1030 | `e7fe894103e9d5a09e91932e248067b20b40281bc3aca74bb4f8564595dd7a24` | 1 | 1 | 2 |

Those envelopes are platform injection, not part of the requested fixed review output and not formal Project Memory evidence. They were not deleted or rewritten, and neither historical commit was amended.

## Isolated runtime provenance

The replacement review ran in a new temporary HOME and CODEX_HOME whose only initial file was the authentication record. The repository was a separate clone fixed at closure HEAD and made filesystem read-only. Codex app-server returned the following actual thread metadata:

- `actual_model=gpt-5.5`
- `reasoning_effort=high`
- `model_provider=openai`
- `ephemeral=true`
- `rollout_path=null`
- `sandbox.type=readOnly`
- `sandbox.networkAccess=false`
- `instruction_sources=[]`
- `approval_policy=never`

History persistence was `none`; no session file was materialized. Memory generation and use, bundled skills and skill instructions, skill search, plugins, remote plugins, apps, multi-agent execution, and prompt templates were disabled. No `MEMORY.md` was loaded. No prior chat was supplied. The historical review raw outputs, metadata, and conclusions were excluded as judgment evidence.

The complete runtime identity and isolation configuration are recorded in `reports/validation/artifacts/project_memory_v0.1_provenance_revalidation_2026-08-02/review_meta.json`.

## Independent implementation revalidation

The isolated review independently recomputed:

- implementation parent `d33a7cfd39a8608524096021ae581a6825bc5cc4` and subject `Implement Project Memory v0.1`;
- exactly 17 implementation paths and exactly 13 `memory/` files;
- all 66 formal evidence objects, with `git show snapshot_commit:path` success and exact SHA-256 identity for every object;
- zero evidence identity failures;
- implementation package SHA-256 `53baa96909e9bf84550f46d28435565613d94cbeda7af9468f72a5b3fd168fed`.

## Independent closure revalidation

The isolated review independently confirmed:

- closure parent `e1723c26efb76bee2aa2b879233a738f4e7e2323` and subject `Seal Project Memory v0.1 implementation closure`;
- exactly 6 closure paths;
- final closure report and manifest agreement on implementation identities, package identity, and sealed state;
- `implementation_closed=true`;
- `closure_effective_on_scoped_commit=true`;
- `state_refresh_required=true`;
- zero nonexistent or future commit references and zero SHA self-reference cycles;
- zero Git, push, trading, business-state, or review-verdict authority grants;
- historical citation envelopes were not treated as formal evidence.

The isolated fixed output has zero memory citation blocks, zero `MEMORY.md:` references, and zero embedded foreign rollout IDs. Its verdict is `GREEN_LIGHT` with `P1=0`, `P2=0`, and `P3=0`.

## Supersession and next boundary

This successful isolated review supersedes only the independent-provenance claims of the two contaminated historical reviews. The historical artifacts and commits remain intact; their other byte identities and repository history are not rewritten.

The implementation and closure records still require a separate state-refresh/provenance remediation commit. Any subsequent state-refresh validation or provenance revalidation must run only after that remediation commit exists. The remediation must reference only already-existing commits and must not prefill a future SHA.

```text
ISOLATION_ENVIRONMENT_VERIFIED=YES
IMPLEMENTATION_COMMIT_MATCH=YES
IMPLEMENTATION_PATH_COUNT=17
MEMORY_FILE_COUNT=13
EVIDENCE_OBJECT_COUNT=66
EVIDENCE_IDENTITY_FAILURE_COUNT=0
IMPLEMENTATION_PACKAGE_SHA_MATCH=YES
CLOSURE_COMMIT_MATCH=YES
CLOSURE_PATH_COUNT=6
REPORT_MANIFEST_STATE_MATCH=YES
IMPLEMENTATION_CLOSED=YES
CLOSURE_EFFECTIVE_ON_SCOPED_COMMIT=YES
STATE_REFRESH_REQUIRED=YES
FUTURE_COMMIT_REFERENCE_COUNT=0
AUTHORITY_GRANT_COUNT=0
P1_COUNT=0
P2_COUNT=0
P3_COUNT=0
VERDICT=GREEN_LIGHT
PROVENANCE_REMEDIATION_COMMIT_READY=YES
STAGED=NO
COMMITTED=NO
PUSHED=NO
```
