# Fable Focused Closure Prompt

审查目标仅限 Sunday Weekly Pipeline v0.1 design r1。请以本包与封存 raw 为证据，逐项确认原 Fable P2-1..P2-4、P3-1..P3-4 是否已被 r1 文字契约和测试矩阵闭合；P3-2 已由 Lucien 升为 P2，须按 P2 阈值审查。

必须重点反证：legacy Review 无 SHA 是否有唯一 fail-closed 落点及完整证据；跨年窗口是否必须加载全部年度并将 SHA 计入 input_set；partial 是否只允许四背景字段并禁止跳日；非法孤儿是否永不补 index/压制新 run；Phase B semantic 是否不能外溢成 SWP no-op；source_time 是否以 Asia/Shanghai 区分市场事实和 provenance 且不可验证即阻断；默认周日/历史显式日期是否闭合；blocked/failed 是否原子且 diagnostics 永不参与 completion。

请输出 GREEN_LIGHT_DESIGN、P1/P2/P3、DESIGN_FREEZE_READY、SOL_HIGH_IMPLEMENTATION_READY，并为每个未关闭 finding 给出精确文件/条款/测试缺口。不要审计实现代码，也不要要求本轮执行任何 runner 或 Git 操作。
