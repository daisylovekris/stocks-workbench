# 锁与诊断路径 r5

唯一 SWP orchestration lock：`<runtime>/locks/sunday_weekly_request_<request_key>.lock`。它始终先于 official facts locks；后者保留并按 canonical pathname 升序获取、释放、同序重取。不得反转 request lock → facts locks，也不得增加第二种 SWP orchestration lock。

早期或阶段 evidence 失败：request-key lock 下 tmp+fsync → `requests/<request_key>/diagnostics/diagnostic_<attempt>` → O_APPEND diagnostics.jsonl+fsync。lock 错误落 `lock-errors/diagnostic_<attempt>`。成功路径在相同锁序下完成 final reread、physical attempt rename 与 index append。
