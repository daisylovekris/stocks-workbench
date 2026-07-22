# 六日 official facts 回填独立验证与 runner 测试隔离

- 验证日期：2026-07-22（Asia/Shanghai）
- 范围：2026-07-15、07-16、07-17、07-20、07-21、07-22 的既有 official facts；`tests/test_run_daily_facts_after_close.py`；本归档。
- 排除：不改 facts 业务字段；不生成 Phase C review manifest；不改 daily review、current 卡、index、weekly；不执行 `git add`、commit 或 push。

## 实际模型日志

- 当前 rollout：`019f89ec-a293-7b01-8362-a2337f25acda`。
- 实际 `turn_context`：`model=gpt-5.6-terra`，`effort=medium`，`cwd=/Users/wongdaisy/Mimo-Lab/stocks`。

## Validator 入口与 rc=2

已先读取 `python3 tools/validate_review_chain.py --help`，并核对 runner 的生产调用：`run_daily_facts_after_close.validator_summary()` 调用 `validate_review_chain.assert_facts_pack_valid()`。CLI 还要求一个 Markdown 输入（`--files` 或 `--staged`），所以每份 facts 用空白临时 Markdown 作为中性 CLI 容器，并传入 `--facts-pack`、目标日和真实前一交易日；同时以生产 `validator_summary()` 作逐份独立复核。

原 `rc=2` 是把 `generate_daily_facts.py` 当作文件 Validator 调用导致的 argparse 用法错误：该脚本是生成器，要求生成参数和输出模式，并不是 official facts 文件验证入口。这不是六份 facts 的 schema 或业务字段失败。

## 六日独立 facts Validator

所有行的 CLI 结果为 `validate_review_chain: PASS | files=1 | P0=0 | P1=0 | P2=0 | P3=0`；生产 `validator_summary` 也均为 `passed`。

| 日期（前一交易日） | 文件 | SHA-256 | schema / trade_date / run.status | P0/P1/P2/P3 | 换手率 | 量比 | source_date |
|---|---|---|---|---|---|---|---|
| 07-15（07-14） | `data/daily/300274_2026-07-15_facts.json` | `0ae94a7d612d2f7c5a35a5f06b5f7e44a4ced95c7f55b89fa049339b5b57c00f` | `facts_pack_v0.2` / `2026-07-15` / `partial` | 0/0/0/0 | present (`3.42`) | `confirmed` (`0.73`) | `2026-07-15` |
| 07-16（07-15） | `data/daily/300274_2026-07-16_facts.json` | `430c05a685712a22ed362a34b7fdaad0bbd843529663b39bc89db741b0ac0984` | `facts_pack_v0.2` / `2026-07-16` / `partial` | 0/0/0/0 | present (`3.94`) | `confirmed` (`0.81`) | `2026-07-16` |
| 07-17（07-16） | `data/daily/300274_2026-07-17_facts.json` | `74731d190a1946df1b79f580c498d2a57b4a191c8d3f8415d8fe9b953e2ab1bd` | `facts_pack_v0.2` / `2026-07-17` / `partial` | 0/0/0/0 | present (`3.92`) | `confirmed` (`0.82`) | `2026-07-17` |
| 07-20（07-17） | `data/daily/300274_2026-07-20_facts.json` | `4ef128d6314383f40263b6cba137ae10a9e7fc5d3353ef109db666e6978b1460` | `facts_pack_v0.2` / `2026-07-20` / `partial` | 0/0/0/0 | present (`4.15`) | `confirmed` (`0.94`) | `2026-07-20` |
| 07-21（07-20） | `data/daily/300274_2026-07-21_facts.json` | `d5049f43f612744558c5e572938e49c60650657991c339627cade2979b3fc071` | `facts_pack_v0.2` / `2026-07-21` / `partial` | 0/0/0/0 | present (`4.22`) | `confirmed` (`0.98`) | `2026-07-21` |
| 07-22（07-21） | `data/daily/300274_2026-07-22_facts.json` | `795a4e77a84fcdebfd5f2f52b088728d86c20833c0d33318c3687298e30ab30a` | `facts_pack_v0.2` / `2026-07-22` / `partial` | 0/0/0/0 | present (`5.34`) | `confirmed` (`1.36`) | `2026-07-22` |

六份的 `missing` 均为 `market_indices`、`sector_context`、`disclosure_status`、`news_policy_context` 四键且值为 `null`；`needs_manual_check` 对这四项均为 `true`、`volume_ratio=false`。四项均属 Phase B partial 白名单的非核心上下文字段；核心行情、换手率、量比与日期一致性没有手工检查阻断。量比验证方法均为受注册的历史五日交叉核验（07-22 为同日快照加 Sohu 五日交叉核验）。

## 测试隔离修复

复现失败：`test_success_manifest_has_full_uuid_finished_stage_and_candidate_sha` 在 dry-run 仍会读取 canonical official 快照；真实仓库已有 07-16 official，故 `official_sha256_before` 不再为 `null`，原测试错误地把真实仓库“文件不存在”当作前提。

修复如下。

- `install_temp_repo_root()` 除了把 runner 的 canonical official 路径指向 `tmp_path/repo/data/daily`，也把共享 `official_facts_lock.DEFAULT_LOCK_DIR` 指向 `tmp_path/repo/.test-locks`；runtime 原本已由 `parse_args()` 指向 `tmp_path/runtime`。
- 该 dry-run 测试现在使用临时 repo，继续断言 absent official 的 before/after SHA 均为 `null`、manifest 完整、candidate SHA 正确。
- 新增 `test_dry_run_snapshot_isolated_from_outside_same_date_official`：在测试外部空间预置同日期 official，runner 仍使用另一临时 repo 和临时 lock，断言外部文件未被读取或改写。
- 没有替换核心事务：runner 的 official snapshot、共享 lock、原子写和 manifest 生产路径仍实际执行。

单项回归：`2 passed`；完整 runner 文件：`120 passed`；与 official lock 一起的 Phase A/B runner 集：`126 passed`。

## 回归与文档 Validator

| 项目 | 结果 |
|---|---|
| `py_compile`（runner、transaction、Validator、该测试） | PASS |
| Phase A/B runner + official lock | `126 passed` |
| Phase C manifest | `122 passed` |
| Generator + Validator + volume-ratio/migration evidence | `250 passed, 24 subtests passed` |
| 全量 pytest | `502 passed, 24 subtests passed` |
| 07-13 facts/review Validator | PASS，P0/P1/P2/P3=0/0/0/0 |
| 07-14 facts/review Validator | PASS，P0/P1/P2/P3=0/0/0/0 |
| 两篇旧 review + 五张 current 卡 | PASS，`files=7`，P0/P1/P2/P3=0/0/0/0 |

## 受保护文件指纹

开工前与回归后的 SHA-256 相同。六份新 facts 的 bytes/SHA 未变，且均与任务给定前缀匹配。

| 受保护对象 | SHA-256 |
|---|---|
| 07-13 facts | `888cdaaa7a3c1b7c4ca5d5ec02d97614f2dd837c0746b2a50b106b091feba3c4` |
| 07-14 facts | `63d1369928c8ab790e7ae53f0b427093af7dc2cfa65475fa676f339d443cbeed` |
| 07-13 review | `9dd9f7403bd97e29997beccbd4e541a134281e2acae2d9ee38b23f9f1a57662f` |
| 07-14 review | `0941e43cdf4be34f8d7bb71d0fa4a0f9e1bb69d3b2f48e19f80fe07869f87392` |
| position card | `fb70ecc64ea0d5d2f5c8d4e6a9bef723899177c2fa71d6db13d9f9e1abc7ca2d` |
| low-zone card | `51f60bfa341efe0993ff0a7d92c34eae64623403c09dda666237d0d5d5f942ed` |
| risk/tracking card | `cb56c4a8897889b5c4c2b6e0beef2eda7aa8870b21bf2f85dafe5e255021decc` |
| add-position card | `0a6374248f2c653c96d397ebb2e79c3360f0c603fbaf31316ae36c24dce04c81` |
| valuation card | `be8d46aad87514a3cfa4d84bb60d7625179301344ce42f884cef43ce2e3aa9ae` |
| index | `d85c3e5cdd9feeb5796b34e38fbc8a7b18994d22164af37eada16622491c90f6` |
| weekly 2026-07-12 | `16bdfa438a8c3d910407547e26ae724261f386078b715e15921a2e9ce4c20a7a` |

## Git 边界与封箱建议

最终 Git 检查：`git diff --check` 与 `git diff --cached --check` 均通过，cached diff 为空。`git status --short` 为本轮修改的 `tests/test_run_daily_facts_after_close.py`、本轮新增的本报告、六份未跟踪 official facts，以及用户既有且明确排除的 `tools/codex-auto.sh`、`repo_harness_readonly_research_notes.md`、`rules/fable_phase_c_external_review_v0.1.md`。本轮未暂存、未提交、未推送。

结论：六份 facts 均独立 Validator PASS，P0/P1/P2 均为 0，受保护 bytes 无漂移；测试隔离已消除真实 07-16 official 的假设。可以作为后续六日 Phase C review manifest 批处理的只读输入：逐日期 official path、上述 SHA、`trade_date/source_date` 一致、`run.status=partial`、四项白名单上下文 `needs_manual_check`、`volume_ratio=false`，以及 P0/P1/P2=0。Phase C 应继续只从 official bytes、有效 runner manifest 和 live Validator 派生，不从本报告或外部运行文本取事实。
