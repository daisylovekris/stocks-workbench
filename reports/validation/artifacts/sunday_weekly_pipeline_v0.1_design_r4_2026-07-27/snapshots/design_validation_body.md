# Sunday Weekly Pipeline v0.1｜设计冻结前验证记录 r4（2026-07-27）

## 结论

r3 包保持原样。本轮仅修订未来实现规格并生成独立 r4 闭包包；未编写实现代码，未暂存、提交或 push。

`P1=0`、`P2=0`、`P3=0`、`FOCUSED_CLOSURE_READY=YES`。本 body 是 identity-free 设计结论：不包含 package、review manifest 或 file manifest SHA。

## r4 修订闭合

| 缺口 | 闭合条款 | 验收 |
|---|---|---|
| r3 包内报告 SHA 自指 | 所有审查材料（含本 body）进入 manifest.files/package；三枚 SHA 只保留在 bundle 外正式报告 | S01 |
| finding mapping 悬空风险 | mapping 静态交叉核验；补回 legacy、Phase C 三分支、跨年与 overlap 测试 | S02、M01、P01-P03、C01-C03 |
| 时间字段来源不明 | facts_pack_v0.2 登记路径内部标准化；未知字段/schema/冲突 fail-closed | T05-T08 |
| 非法 request 字段处理不一致 | 四字段统一 valid/invalid safe envelope；原值不进路径、日志、诊断正文 | I01、I06-I09 |
| 锁语义分裂 | 全规则仅 request-key lock | L01 |

## 原始 finding 连续性

Fable P2/P3、r2 与 r3 新 finding 都在 `finding_mapping.md` 中有至少一个真实 test_matrix ID；测试矩阵同时涵盖物理 completion identity、early diagnostics、calendar coverage、Phase C 精确白名单与 typed time contract。

## 边界

本轮设计层验证不执行未来实现测试或 external focused closure；后者应以本包及 bundle 外身份 SHA 进行。
