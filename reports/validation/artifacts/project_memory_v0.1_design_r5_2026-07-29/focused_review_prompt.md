# Focused Fable review: Project Memory v0.1 design r5

Review only the r5 mother package. Read `design_manifest.json` first. Independently recompute the byte size and SHA-256 of every `sealed_files` member, then independently recompute `design_package_sha256` using the manifest's declared algorithm. Confirm that the manifest itself is excluded from `sealed_files`, and that the exact sealed member set and counts are correct.

Verify the Phase, Agent, ADR, conflict matrix, `project_state`, and non-authority boundaries against the sealed files. Verify there is no self-commit loop and that no `memory/` was created. Do not modify files, stage, commit, push, create `memory/`, or run production code.

Classify findings as follows:

- P1 blocks safety or identity.
- P2 blocks contract completeness.
- P3 is non-blocking.

Only `P1=0` and `P2=0` permit `GREEN_LIGHT`.

Output a fixed verdict matrix containing: `verdict`, `P1`, `P2`, `P3`, and exact evidence. The verdict must explicitly report the independent results for member-set match, payload/artifact counts, all sizes, all file SHA-256 values, package SHA-256, manifest exclusion, main-report inclusion, focused-prompt inclusion, and `.DS_Store` exclusion.
