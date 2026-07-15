# 正式 facts 写入锁与迁移 profile 封箱终审

归档日期：2026-07-16

最终两项封箱修补已完成。三条正式 facts 写入路径现在覆盖完整锁内事务，07-13 已具备与 07-14 同等级的持久负向矩阵。

## 1. 三条路径修改前后的锁边界

- 生成器：由“锁外读取、组装，仅锁最终写入”改为短锁固定 expected SHA，远程准备后再以完整长事务完成读取、解析、组装、真实 Validator、临时写入、替换、目录同步和写后 SHA（`tools/generate_daily_facts.py:1677`、`tools/generate_daily_facts.py:1765`）。
- AKShare：由锁外构造 payload、锁外读取 SHA 改为锁内读取旧对象、构造最终 payload、结构校验、替换和写后指纹（`tools/akshare_daily_quote_check_v0.1.py:376`）。
- Promote：主体保持不变，最终 bytes 和 SHA 已移入释放锁之前（`tools/migrate_legacy_volume_ratio_evidence.py:945`）。

## 2. 仍在锁外的动作

仅保留与旧 official 内容无关的准备：

- 行情查询、诊断查询和量比原始候选准备；
- promote 候选文件的固定 bytes 与候选 SHA 校验；
- 非写入流程的控制台输出。

生成器和 AKShare 在远程准备前仅用短锁记录 expected SHA；正式写入阶段重新取得同一目标锁并完整重读。没有把远程查询放进长事务，也没有增加循环核对或无限重试。

## 3. 生成器锁内流程

锁内依次完成：

1. expected SHA 重核；
2. official bytes 读取及 JSON、标的、日期校验；
3. manual/sealed 保护与最终 facts 组装；
4. 状态和覆盖条件计算；
5. 调用真实 review-chain facts Validator（`tools/generate_daily_facts.py:1699`、`tools/validate_review_chain.py:1219`）；
6. 临时文件写入与 fsync；
7. official SHA 再核对；
8. 原子替换及目录同步；
9. 写后 bytes 和 SHA 读取并与本次候选核对（`tools/generate_daily_facts.py:1714`）。

最终 SHA 写入 `RunOutcome.output_sha256`。

## 4. AKShare 锁内流程及校验

AKShare 的冻结 `facts_pack_v0.1` 不具备新版 review-chain Validator 要求的方法级证据字段，因此没有放宽 Validator，而是增加独立最小结构门禁（`tools/akshare_daily_quote_check_v0.1.py:276`），核对：

- 固定 schema；
- 标的与日期；
- quote 精确字段和数值类型；
- 量比状态范围；
- `missing`、`needs_manual_check` 精确键集合；
- JSON 可序列化且无非法数值。

查询结果仍在锁外准备；payload 构造、结构校验、写入和最终 SHA 全部位于锁内。输出 schema 和诊断含义未改变。

## 5. Promote 锁内最终 SHA

原子替换和目录同步后，promote 在仍持锁时读取正式目标，确认：

- 最终 bytes 等于固定候选 bytes；
- 最终 SHA 等于候选 SHA；
- 返回值直接使用锁内保存的 SHA。

释放锁后不再重读目标作为本次结果指纹。

## 6. 锁持有状态测试

共享锁 context 现在暴露只读 `held` 状态（`tools/official_facts_lock.py:33`）。

测试已证明以下动作发生时 `held=True`：

- 生成器：读取、SHA、解析、组装、Validator、临时写入、替换、写后读取和 SHA（`tests/test_official_facts_lock.py:174`）。
- AKShare：读取、SHA、解析、payload 构造、结构校验、临时写入、替换和写后 SHA（`tests/test_akshare_daily_quote_check.py:76`）。
- Promote：读取、真实 Validator、profile compare、替换和最终 SHA（`tests/test_migrate_legacy_volume_ratio_evidence.py:667`）。

## 7. 并发测试

锁状态与并发定向结果：`7 passed`。

覆盖：

- 生成器与生成器：第二个等待，取得锁后旧 SHA 失效并停止，第一份结果保留（`tests/test_official_facts_lock.py:80`）。
- AKShare 与 promote：后取得锁的一方因旧 SHA 失效停止（`tests/test_migrate_legacy_volume_ratio_evidence.py:1025`）。
- Promote 写后 SHA 阶段：第二写入者仍等待；promote 返回的 SHA 精确对应本次候选；释放后第二写入者才运行（`tests/test_migrate_legacy_volume_ratio_evidence.py:1107`）。
- 锁内 Validator 异常：official 不变、无临时残留，后续写入正常（`tests/test_official_facts_lock.py:139`）。

## 8. 07-13 负向矩阵

20 项持久矩阵全部通过拒绝验证（`tests/test_migrate_legacy_volume_ratio_evidence.py:822`）。

每项均证明：

- Validator 或 profile compare 拒绝；
- official bytes 与 SHA 不变；
- 无 `.promote-*`、`.tmp` 或同目录 `.lock`；
- profile 外新增、对象删除、类型变化、两来源 check、来源标识、日期/成交量序列、计算值、容差、公式、迁移元数据和固定上下文字段全部受控。

07-13 首次 promote 使用真实 Validator 成功（`tests/test_migrate_legacy_volume_ratio_evidence.py:263`），合法候选和重复 no-op 继续通过。

## 9. 07-14 矩阵回归

原 20 项候选字段矩阵全部通过（`tests/test_migrate_legacy_volume_ratio_evidence.py:755`）。

双 profile 矩阵、合法候选和 no-op 合计定向结果：`42 passed`。

## 10. 正式 facts 与复盘链

- 07-13 Validator：`PASS | P0=0 | P1=0 | P2=0 | P3=0`
- 07-14 Validator：`PASS | P0=0 | P1=0 | P2=0 | P3=0`
- 两份 reviews + 五张 current 卡：`PASS | files=7 | P0=0 | P1=0 | P2=0 | P3=0`

正式 facts SHA 未变化：

- 07-13：`888cdaaa7a3c1b7c4ca5d5ec02d97614f2dd837c0746b2a50b106b091feba3c4`
- 07-14：`63d1369928c8ab790e7ae53f0b427093af7dc2cfa65475fa676f339d443cbeed`

OHLC、成交额、换手率、量比、原始来源、原始时间及 `partial` 状态均未改变。

## 11. 全量测试

- 生成器：`73 passed, 22 subtests passed`
- Validator + 量比证据：`102 passed`
- 锁、AKShare、迁移、profile 定向：`97 passed`
- 全量：`252 passed, 22 subtests passed in 7.29s`
- `py_compile`：通过
- `git diff --check`：通过
- `git diff --cached --check`：通过

## 12. Git 状态

- `git status --short` 路径集合与本轮开始时一致，状态指纹为 `0dcf97e04c1c60b119f97c943ec8c7cb6196610e198938152ec6c15aaf5247bc`。
- 终审核验时暂存区为空。
- 终审核验未执行 `git add`、commit 或 push。
- 既有 review、current 卡、索引和范围外文件未被终审核验修改或清理。
- 复现材料位于 `/private/tmp/stocks_final_seal_20260716`。

## 13. P1/P2

本轮正式 facts 写入事务边界与 07-13 profile 持久测试范围内未发现剩余 P1/P2。

保留的边界说明不变：只有遵守共享锁约定的仓库内写入者属于该并发模型；不对绕开约定的外部写入声明基于内容哈希的原子条件更新保证。

## 14. 极小只读核验摘要

三条正式写入入口现均在锁内完成 official 重读、校验、最终组装、写入、替换及写后 SHA；远程准备保持锁外。07-13、07-14 各 20 项负向矩阵通过，正式 facts 与七份复盘材料 PASS，全量 `252 passed, 22 subtests passed`，正式业务数据 SHA 不变，终审核验时暂存区为空。
