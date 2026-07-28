# Fable Focused Closure Prompt r2

审查目标**仅限** Sunday Weekly Pipeline v0.1 design r2，且仅可读取本 bundle payload；不得读取 r1 包或任何 r1 外部材料，不审计实现代码，不要求 runner、Git 或网络操作。

Fable raw 快照路径为 `snapshots/fable_raw.md`，其 SHA-256 必须为 `4cafde436432a20e843c0e39b981beda938a956341c40e17a9eb9743d684fd79`。先核对该 SHA，再只针对 r2 规则快照、验证报告快照、finding 映射、状态矩阵、测试矩阵和写锁顺序，逐项反证：真实 calendar coverage/trading_days 是否没有把缺 coverage 静默视作非交易日，跨年/重叠是否 fail-closed；Phase C 是否仅允许两个精确 state；diagnostic identity、目录、JSONL 写锁和 lock_error evidence 是否完整且不参与 completion。

确认原 Fable P2-1..P2-4、P3-1..P3-4 及 r2 新增 calendar P2、三项 P3 均有唯一条款与测试。输出 `P1`、`P2`、`P3`、`FOCUSED_CLOSURE_READY`；任何未闭合项必须给出本包内精确文件、条款和测试缺口。
