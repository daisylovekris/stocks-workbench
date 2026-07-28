# 现有模块地图

| 模块/样本 | 作用 | SWP 用法 |
|---|---|---|
| `weekly/weekly_market_watch_2026-07-19.md` | 人工周观察先例 | 提取非交易建议、观察层级和人工纪律边界 |
| `weekly/weekly_market_watch_2026-07-26.md` | 五日黄金样本 | 确定统计字段、Daily Review 关联和 TODO/null 表达 |
| `reports/validation/sungrow_weekly_observation_2026-07-26_validation.md` | 人工核验基线 | SHA、复算、future scan、五卡核对证据形态 |
| `tools/validate_review_chain.py` | facts Validator | 每份 inputs 的现场强制门 |
| `tools/phase_b_completion.py` | 已完成记录的实时语义核验 | 采用 fail-closed completion 逻辑 |
| `tools/review_manifest.py` + Phase C rules | runtime/manifest/index/权限先例 | 只读检查 Phase C，沿用权限关闭与原子提交理念 |
| `tools/safe_file_read.py` | anti-symlink/FD 安全读 | 所有不可信输入读取 |
| `tools/official_facts_lock.py` | official facts 排他锁 | 输入快照及最终 SHA 复读 |
| `config/a_share_trading_calendar_2026.json` | 正式交易日 | 推导上一完整周，支持短周 |
| 五张 current 卡、`stock_workbench_index.md` | 人工上下文 | 仅用于人工审阅核对；SWP 不读取来填机器判断、不写入 |

不存在独立“weekly validator”可直接授权机器写周观察；现有 `validate_review_chain.py` 是 facts/review-chain validator。SWP 因此应新增候选 schema validator，而不把既有 Markdown lint 误作交易/授权 validator。

