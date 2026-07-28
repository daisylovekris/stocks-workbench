# 状态矩阵 r5

| 状态 | r5 reason | 权限 | 必需证据 |
|---|---|---|---|
| `blocked_identity_conflict` | `phase_b_evidence_missing` / `phase_b_evidence_invalid` / `phase_c_evidence_missing` / `phase_c_evidence_invalid` 及既有 identity reasons | 全 false | expected canonical path、actual path、raw SHA、schema/identity finding、available_inputs、missing_inputs、request key |
| `candidate_ready_for_human_review` | all gates passed | only human_review=true | input set 含 daily Phase B/C SHA + semantic config SHA |
| `already_completed` | matching completion / recovery | no upgrade | 现场复算 input set、semantic config 与 evidence SHA |
| all other blocked/failed | existing reasons | 全 false | 既有 fail-closed evidence 加 request-key diagnostics |
