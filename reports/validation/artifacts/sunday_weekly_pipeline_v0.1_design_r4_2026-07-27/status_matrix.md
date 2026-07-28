# 状态矩阵 r4

| 状态 | reason | 权限 | r4 关键证据 |
|---|---|---|---|
| `candidate_ready_for_human_review` | `candidate_created:all_gates_passed` | human_review=true；其余 false | semantic key、attempt、index 六字段 |
| `blocked_missing_facts` | `facts_missing:<date>` | 全 false | request_key、safe envelope、available/missing inputs |
| `blocked_missing_daily_review` | `daily_review_missing:<date>` | 全 false | request_key、safe envelope、expected review |
| `blocked_invalid_facts` | calendar/as_of/metrics reasons | 全 false | request_key、calendar diagnostics |
| `blocked_future_data` | `future_input_detected` / `source_time_unverifiable` | 全 false | normalized source_kind、registered path、structured time or failure |
| `blocked_identity_conflict` | Phase C/ambiguous orphan/identity reasons | 全 false | safe identity, enum or orphan inventory |
| `already_completed` | matching completion / index recovered | no upgrade; trading=false | index exact fields + full revalidation |
| `failed` | lock/runtime reasons | 全 false | request_key, unique attempt, atomic evidence |

All diagnostic paths use the one request-key lock contract and contain no raw invalid request field values.
