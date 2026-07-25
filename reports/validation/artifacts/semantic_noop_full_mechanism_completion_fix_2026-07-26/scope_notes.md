# semantic_noop completion fix review scope

## Frozen identity

- Base HEAD: `877e20aa8b1601ed92ed934f8bcd8300c5039845`.
- Candidate: base HEAD plus `scoped_completion_fix.patch`.
- The patch contains the prior semantic_noop full mechanism and this completion-fix delta; routing changes, formal 2026-07-23 facts, unrelated reports, and other user worktree files are excluded.
- The old `semantic_noop_full_mechanism_2026-07-25` bundle is retained and marked superseded; its original 18 sealed payload files and recorded package SHA are not overwritten.

## In scope

- Phase B semantic transaction and generator mapping.
- Phase B runner completion scan, completion validation, diagnostics, bundle-failure recovery, and runner-lock ordering.
- Shared Phase B action/outcome/reason matrix.
- Shared no-follow fd evidence reader.
- Phase C import of the shared matrix/fd reader, with no expansion of failed bundles into normal facts reviews.
- Rules and tests directly exercising these paths.

## Complete dependency snapshots

The bundle includes full source snapshots for the in-scope files and the real lock, facts Validator, timezone evidence parser, trading calendar, Phase C rule, and Phase C tests. Reviewers need not infer the three dependencies omitted from the superseded bundle.

## Explicitly deferred

- K3 P3-2: standalone `generate_daily_facts --write-official` transaction-result reporting.
- K3 P3-3: partial semantic_noop runner `needs_manual_review` consistency.
- Directory-wide atomic commit of summary/manifest bundles.

## Test collection boundary

The repository contains preserved audit snapshots named `snapshots/tests/test_*.py`. A bare repository-root `pytest` therefore imports duplicate module basenames. The authoritative full-suite command is `PYTHONPATH=. pytest -q -p no:cacheprovider tests`; both the main worktree and the clean Git candidate use that explicit test root.
