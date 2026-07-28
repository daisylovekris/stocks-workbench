# 模块地图 r1

| 模块/样本 | SWP 契约用途 | r1 边界 |
|---|---|---|
| `config/a_share_trading_calendar_<year>.json` | 正式交易日窗口 | 加载窗口涉及的全部年度；逐日显式标记；全部 raw SHA 入 input_set |
| `tools/validate_review_chain.py` | facts schema/数值现场校验 | partial 仅四背景字段；metrics 缺失/非法 fail-closed |
| `tools/phase_b_completion.py` | completion 全量现场重验范式 | 不把 Phase B semantic 结果当 SWP no-op 身份 |
| `tools/review_manifest.py` + Phase C rules | manifest、权限关闭先例 | 仅作为 G4/G7 输入；不授权 SWP 写 Phase C |
| `tools/safe_file_read.py` | no-follow/FD 安全读 | calendar、facts、review、manifest、runtime 均须安全读 |
| `tools/official_facts_lock.py` | facts 锁与最终复读 | weekly lock 后 pathname 升序；两次快照闭合 TOCTOU |
| `weekly/weekly_market_watch_2026-07-26.md` | 人工观察黄金样本 | 只供人工格式/事实交叉核对，不作机器写 weekly 授权 |

没有可复用的 SWP runner、candidate schema 或 weekly writer；本包仅定义未来实现契约。
