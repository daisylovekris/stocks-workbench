# 状态矩阵 r6

| 状态/reason | 权限 | 证据 |
|---|---|---|
| `blocked_identity_conflict:phase_c_evidence_missing` | 全 false | review index path、available/missing inputs。 |
| `blocked_identity_conflict:phase_c_evidence_invalid` | 全 false | index entry inspection、manifest path/SHA finding。 |
| `blocked_identity_conflict:ambiguous_phase_c_authority` | 全 false | conflicting valid authority inventory。 |
| `blocked_identity_conflict:phase_b_evidence_missing` | 全 false | authenticated Phase C runner fields/rebuild provenance。 |
| `blocked_identity_conflict:phase_b_evidence_invalid` | 全 false | Phase B raw SHA + completion validator finding。 |
| success/no-op | no permission upgrade | resolver chain + config raw SHA live revalidation。 |
