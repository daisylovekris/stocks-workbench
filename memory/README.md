# Project Memory v0.1

## Purpose

Project Memory is a small navigation layer over repository evidence. It points to authoritative rules, facts, cards, reviews, daily reports, weekly reports, indexes, validations, and closures without copying or replacing their authority.

## Non-authority boundary

Memory does not override any rule, fact, card, daily report, weekly report, index, validation, or closure. It grants no trading authority, Git authority, business-state authority, or review-verdict authority. A Memory entry proves only what its cited bytes say at the cited commit; it cannot approve, execute, supersede, or reverse-write a source.

## Files

- `memory/project_state.md` records the current project milestone, queues, exclusions, and closure references.
- `memory/phase_registry.md` records the exact seven-phase registry.
- `memory/agent_benchmark.md` records the exact nine Agent/model subjects and their bounded evidence status.
- `memory/decisions/ADR-0001.md` through `memory/decisions/ADR-0009.md` record the frozen decision seeds without changing their status.

No `memory/manifest.json`, copied source inventory, or production validator belongs to this implementation candidate.

## Evidence identity

Every formal evidence object is commit-bound and contains exactly:

- `path`: a repository-relative path;
- `snapshot_kind`: `commit`;
- `snapshot_commit`: the real 40-character commit containing the cited bytes;
- `raw_sha256`: the real SHA-256 of `snapshot_commit:path`;
- `role`: the evidence role in the current record.

Worktree-only evidence, absolute paths, symbolic source IDs, summaries without byte identity, future commit identities, and references to a not-yet-existing implementation commit are prohibited.

## Update workflow

Check idempotency first. Locate the repository authority by class, verify its commit-bound identity, and change only the smallest affected Memory record. Validate the worktree before any separately authorized staging. Any later closure must use precise path staging, index validation, independent review where required, commit-tree validation, and the default no-push policy.

Ordinary chat is not a synchronization trigger. Chat must never be copied into Memory automatically, and Memory must never modify an authoritative source in reverse.

## Prohibited uses

- Do not infer or generate trading conclusions, buy/sell instructions, price triggers, or position actions.
- Do not grant staging, commit, push, business-state, permission, or review-verdict authority.
- Do not turn routing policy or a single observed run into a general model ranking.
- Do not import credentials, tokens, cookies, authorization headers, or external runtime state.
- Do not use Memory to replace, rewrite, or supersede repository authorities.
- Do not push by default; push always requires separate explicit authorization.

