# 测试矩阵

| # | 情形 | 核心断言 |
|---|---|---|
| 1 | 正常五交易日 | ready；逐项 metrics/SHAs/五 reviews；所有交易权限 false |
| 2 | 节假日短周 | calendar 的 2—4 日集合被接受；不要求五日 |
| 3 | facts 缺一天 | `blocked_missing_facts`；无 candidate/index |
| 4 | facts SHA 漂移 | `blocked_invalid_facts`；最终提交前失败 |
| 5 | Daily Review 缺失 | `blocked_missing_daily_review` |
| 6 | Daily Review 引用未来事实 | `blocked_future_data`，保存 offender |
| 7 | TODO/null 背景 | 原样在 candidate unresolved_fields；不得补值 |
| 8 | 数值复算 | Decimal 周 OHLC、涨幅、amount/turnover/volume-ratio aggregates 精确匹配 |
| 9 | 人工字段为空 | 仍 ready；每个字段 owner 正确、value=null |
| 10 | 非法自动交易字段 | schema 拒绝，`blocked_identity_conflict` |
| 11 | candidate 重跑 | 相同 input set 返回 `already_completed`，不改 bytes |
| 12 | semantic no-op | 合法 Phase B semantic evidence 可通过；不放宽重验 |
| 13 | manifest 提交失败后重跑 | tmp/孤儿不算完成；恢复为一次完整提交 |
| 14 | forged completion | 假 index/损坏 manifest/旧 SHA 不 suppress；重新执行 |
| 15 | 双进程竞争 | 仅一个 index final marker；另一方等锁后 no-op 或重验 |
| 16 | 其他股票零改动 | symbol A 运行不读写 symbol B 或正式业务文件 |

每例同时断言 outcome、reason_code、evidence、downstream permissions、runtime 路径安全和正式 `weekly/` 零写入。

