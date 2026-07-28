# 锁与 authority 路径 r6

唯一 SWP orchestration lock 是 `<runtime>/locks/sunday_weekly_request_<request_key>.lock`。它在 official facts locks 之前获取；facts locks 保留 canonical-pathname 升序、释放后同序重取。Phase C resolver 读取 `<runtime>/reviews/<trade_date>/review_index.jsonl`，再由已验证 manifest 指向真实 Phase B `runs/<trade_date>/<run_id>/manifest.json`。不存在 symbol-hash Phase B/C 路径。
