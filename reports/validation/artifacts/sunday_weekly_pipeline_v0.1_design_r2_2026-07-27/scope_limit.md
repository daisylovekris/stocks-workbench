# 范围限制 r2

本包是设计冻结前 focused closure 的只读输入。它不实现 runner、schema、validator、scheduler 或任何生产代码；不修改 official facts、Daily Review、weekly、current cards、repo index；不执行 `git add`、commit、push。

r1 包 `reports/validation/artifacts/sunday_weekly_pipeline_v0.1_design_r1_2026-07-27/` 保持原样。r2 外审只准读取本 bundle 的 payload，尤其不得读取 r1 外部材料；本规则中 runtime 写入描述都是未来实现契约，不代表本轮曾写入 runtime。
