# 给 Fable 的独立架构窄审提示

请只审查 `rules/sunday_weekly_pipeline_v0.1.md` 与本包，独立判断，不执行代码、不联网、不改文件。

请重点寻找 P1/P2/P3：

1. 是否存在任何路径让机器把 candidate 当正式 weekly、批准、交易信号或 Phase C 权限升级？
2. 准入门能否防止漏交易日、身份错配、facts SHA 漂移、Daily Review 缺失/未来信息和 TODO/null 被猜测补齐？
3. completion/semantic no-op 是否足够 fail-closed，伪造或损坏 manifest/index 是否会错误 suppress 新运行？
4. 双进程、facts 多锁顺序、最终 SHA 复读、atomic rename/index 顺序是否会产生半完成或死锁？
5. 短交易周、跨年 calendar、legacy Daily Review facts-SHA 缺失应如何保持安全？

输出请按 `P1/P2/P3 | 位置 | 可复现场景 | 风险 | 最小修复`；未发现时明确写 `P1=0/P2=0/P3=0` 并说明审查范围。不得把历史样本文字润色为新事实。

