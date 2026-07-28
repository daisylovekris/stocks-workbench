# Focused Closure Prompt r3

仅审 Sunday Weekly Pipeline v0.1 design r3，只读取本 bundle，尤其不得读取 r2 包或任何 r2 外部材料；不审实现代码，不要求执行 runner、Git、网络或 Fable 调用。

先核对 `snapshots/fable_raw.md` SHA-256=`4cafde436432a20e843c0e39b981beda938a956341c40e17a9eb9743d684fd79`，再审 rules/report snapshots、finding mapping、identity diagram、状态/测试矩阵与写锁路径。重点反证：input-set 前 calendar/facts/review/Phase C/lock 错误能否仅用 request_key 保存证据且不泄漏路径 token；completion 是否由 semantic key 与 unique physical attempt 分离、index 是否精确、损坏/重复孤儿是否 fail-closed；source kind 与时间格式是否机器可读且自由文本不能放行；任何 calendar overlap 是否一律阻断。

输出 `P1`、`P2`、`P3`、`FOCUSED_CLOSURE_READY`。未闭合项必须给出本包内精确文件、条款、测试缺口。
