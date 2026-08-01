# Update workflow

This is a future manual workflow contract. r5 does not execute staging, commit, push, validator implementation, or Memory implementation.

## 1. Idempotency and trigger

Check whether the exact source identity and intended Memory state are already recorded. Exit without model, network, or Git-write work when there is no semantic change.

Valid triggers are:

- phase design, implementation, validation, or closure;
- final independent review;
- owner-authorized ADR or explicit supersession;
- a commit-bound observed agent run;
- project milestone or work-queue movement;
- deferred-work closure; or
- correction of a stale, missing, or conflicting evidence identity.

Ordinary chat, an unbound routing label, a new market observation, or an unchanged source is not by itself a Memory update trigger.

## 2. Locate authority

Resolve the current repository authority by class before editing Memory. Bind every claim to the inventory entry containing repository-relative path, `snapshot_kind=commit`, full snapshot commit, raw SHA-256, role, and any separate sealing commit.

If a path is absent, a hash differs, authority classes conflict, or the required model/run identity is missing, stop with the applicable fail-closed status. Do not infer the missing value from a summary, filename, chat message, later date, or UI label.

## 3. Select the minimum modification set

Update only the affected fixed-heading record and the smallest necessary navigation/index references. Do not rewrite unrelated history, regenerate all Memory files for a local change, or reverse-write a Memory summary into an authority source.

For an identity-only refresh, preserve decision text and status unless separate evidence authorizes a semantic change. For a status, ADR, benchmark, permission-boundary, or supersession change, require independent review.

## 4. Worktree validation

Run the read-only validator in `--worktree` mode before staging. Validate schemas, exact sets, enums, path membership, commit/hash identity, evidence completeness, conflict handling, authority boundaries, sensitive-information rules, Markdown structure, and intended package membership.

Keep known dirty exclusions outside the candidate path set. A failure blocks staging; fix only the scoped Memory artifacts and rerun. Do not run broad formatters over unrelated files.

## 5. Precise staging

Stage only the explicitly reviewed paths, using an exact path list. Never use broad staging such as `git add .`, `git add -A`, a directory-wide wildcard, or an unresolved generated list.

Immediately inspect the cached path list and cached diff. Any unexpected path, deletion, rename, generated secret, or unrelated dirty file requires unstaging the candidate and returning to worktree validation.

## 6. Index validation

Run the same read-only validator in `--index` mode against exactly the staged bytes. Worktree success does not substitute for index success. The index must contain the intended complete package membership, no extra paths, and the same evidence relationships reviewed in the worktree.

## 7. Independent review

Obtain independent, source-bound review for any decision, authority boundary, phase status, closure status, benchmark admission, or supersession change. Routing policy is not independent-review evidence. Diagnostic runs remain excluded unless a later explicit adjudication admits a different, fully bound run.

## 8. Commit and commit validation

After worktree validation, precise staging, index validation, and required review all pass, create one scoped commit. Then run the validator in `--commit <sha>` mode against the committed tree and verify the expected path set.

The identity order is:

1. review and separately commit the design closure;
2. generate Memory implementation citing that pre-existing design-closure commit;
3. commit the Memory implementation;
4. generate any later closure report citing that pre-existing implementation commit.

No file contains its own future commit SHA.

## 9. Default no-push

The default terminal state is a locally validated commit with no push. Push requires separate explicit user authorization and is not implied by design approval, validation success, review success, or commit creation.

## 10. Retry boundary

Check idempotency before every retry. Retry only a failed, transient step; do not repeat successful model reviews, network calls, or full repository scans. Use a finite retry limit and stop with the exact failure after the limit. Retain a manual recovery path.

## Prohibitions

- Never synchronize chat into Memory automatically.
- Never infer or generate trading conclusions, buy/sell instructions, price triggers, or position actions.
- Never change phase or ADR status without exact authority.
- Never turn routing policy or one observed run into a general model ranking.
- Never copy secrets, credentials, cookies, tokens, authorization headers, or external runtime state into the repository.
- Never broaden the task scope through staging, commit, push, or source rewrites.

## Quota and repeated-execution cost

Normal idempotent link refresh is expected to be low consumption. Closure, ADR, or benchmark changes are medium consumption because source comparison and independent review dominate. Use local inventory/cache checks, deterministic validation, bounded context, no duplicate schedules, no polling after success, and no repeated full review when bytes are unchanged.
