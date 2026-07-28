# Sunday Weekly Pipeline v0.1 r14 final contract errata

r13 remains unchanged. No production runtime implementation was added; no staging, commit or push occurred.

- G1 now separates valid zero-trading windows from invalid calendar coverage. The former is no_candidate_for_window/no_candidate/no_trading_days/all false, diagnostic only.
- Main rule, status matrix and finding mapping use state/outcome/reason_code/permissions tuples.
- Tuple static evidence records both tuple sets, empty set differences and no mapping tuple/permission mismatch.
- The R13 candidate-created mapping now has human_review only. Blocked, failed and no-candidate are all false; already_completed inherits original candidate with trading false.
- Phase B execution evidence now records execution driver, driver SHA, invocation, process exit, stdout/stderr and direct function returns; 07-23 direct return is semantic_noop.
- Validation dependency names the candidate schema snapshot and raw SHA; module map lists path/size/SHA/contract/boundary.

Recomputed identities:

- package SHA-256: e2301e00fb97a1b1383ba13ec1400693c265984370eb6c74ae0c0eccc6522f6d
- review manifest SHA-256: 855d78da78fd373156e76a2394c00532c6bb557521f22d84637a0bdd3d741df6
- file manifest SHA-256: 24c1fc60f8a71710f3d98e0aa6039b56039124af229a791ccc68dd59af0a7911
- golden input-set SHA-256: 9af2c2dbe1b6556bcf4c2fc332d45f3a31131f1933f2d75963c6fa505af17293
- golden candidate SHA-256: ae5d74c61ab6cda5e5adf44db33607f314d21873a585fb5564518aaff5018b03

P1=0; P2=0; P3=0; FULL_DESIGN_CLOSURE_READY=YES; FABLE_FULL_CLOSURE_READY=YES.
