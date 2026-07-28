# 测试矩阵 r5

| ID | 情形 | 断言 |
|---|---|---|
| R01 | legacy Daily Review | 无 facts SHA -> fail-closed。 |
| R02 | 跨年双 calendar | 合并成功，SHA 全入 input set。 |
| R03 | partial metrics 缺失 | 不聚合。 |
| R04 | 合法孤儿 | full revalidation 后 index recovery。 |
| R05 | SWP 输入变更 | 不被 Phase B semantic-pass suppress。 |
| R06 | Shanghai as_of | 周日/显式历史模式确定。 |
| R07 | 早期诊断 | request_key/attempt 原子且不泄漏 raw。 |
| R08 | calendar overlap 同/异分类 | 均阻断。 |
| R09 | Phase C states | two accepted success; unknown/null/empty/other block。 |
| R10 | diagnostic concurrency | request lock 下 JSONL 完整。 |
| R11 | completion attempts/orphans | 损坏不占位；双合法孤儿 fail-closed。 |
| R12 | invalid request envelope | 四字段非法仍可 request-key diagnostic。 |
| R13 | package sealing | 每一审查材料进入 package SHA。 |
| R14 | lock contract | 无第二种 SWP orchestration lock。 |
| B01 | Phase B evidence missing | `blocked_identity_conflict:phase_b_evidence_missing`；expected/actual path、available/missing inputs。 |
| B02 | Phase B evidence invalid | `phase_b_evidence_invalid`；raw SHA、schema/identity finding。 |
| B03 | Phase B evidence SHA changes | 新 input set；manifest/revalidation 比较新 SHA。 |
| C01 | Phase C evidence missing | `phase_c_evidence_missing`；完整 diagnostic fields。 |
| C02 | Phase C evidence invalid | `phase_c_evidence_invalid`；完整 diagnostic fields。 |
| S01 | semantic config changes | candidate schema/whitelist/time/cutoff 任一变更 -> 新 input set。 |
| S02 | semantic config live revalidation | manifest 包含 SHA，现场重算不符不 no-op。 |
| T01 | typed RFC3339 | offset/Z 转 Shanghai；naive/date-only/free text fail-closed。 |
| T02 | registry contract | unknown schema/unregistered field/path conflict fail-closed。 |
| T03 | sealed golden provenance | 黄金样本的 07-25 generated_at/fetched_at 是合法 provenance。 |
| T04 | sealed golden daily_bar | 黄金样本 trade_date/source_date/trade_dates 是 daily_bar。 |

每例断言状态、reason、全 false 或不升级权限、安全路径、原子性及正式 weekly 零写入。
