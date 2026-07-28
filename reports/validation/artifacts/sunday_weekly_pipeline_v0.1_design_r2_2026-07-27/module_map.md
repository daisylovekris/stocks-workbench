# 模块地图 r2

| 模块/样本 | SWP 契约用途 | r2 边界 |
|---|---|---|
| `config/a_share_trading_calendar_<year>.json` | coverage + `trading_days` 的正式窗口 | 加载所有涉及年度；每个窗口日恰一 coverage；全部 classifying raw SHA 入 input_set。 |
| `tools/validate_review_chain.py` | facts schema/数值现场校验 | partial 仅四背景字段；metrics 缺失/非法 fail-closed。 |
| `tools/phase_b_completion.py` | completion 全量现场重验范式 | 不把 Phase B semantic 结果当 SWP completion 身份。 |
| `tools/review_manifest.py` + Phase C rules | Phase C evidence/权限关闭先例 | G7 精确白名单仅两种 state；不授权 SWP 写 Phase C。 |
| `tools/safe_file_read.py` | no-follow/FD 安全读 | calendar、facts、review、manifest、runtime 均须安全读。 |
| `tools/official_facts_lock.py` | facts 锁与最终复读 | weekly lock 后 pathname 升序；两次快照闭合 TOCTOU。 |
| runtime `diagnostics.jsonl` | 诊断审计流 | weekly lock + O_APPEND + fsync；永不作为 completion。 |

没有可复用的 SWP runner、candidate schema 或 weekly writer；本包只定义未来实现契约。
