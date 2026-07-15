# Fable 外部审稿单：`generate_daily_facts.py` P2 封箱复核

请以外部审稿人身份，对下面这轮改动做一次只读、findings-only 的封箱复核。

本次不是请你重写方案，也不是泛泛评价代码风格。请优先寻找会导致错误 `confirmed`、跨交易日串值、证据字段失真或 fail-open 的具体问题。

## 一、审稿范围

只审以下两个文件的当前 diff：

- `tools/generate_daily_facts.py`
- `tests/test_generate_daily_facts.py`

工作区还有其他未提交改动，与本次 P2 封箱无关，请不要把它们纳入结论，也不要建议回滚或修改它们。

建议使用：

```bash
git diff -- tools/generate_daily_facts.py tests/test_generate_daily_facts.py
```

重点调用链：

- `OHLC_FIELDS`
- `_quote_values_match()`
- `_same_day_snapshot_ohlc_matched()`
- `fetch_tencent_direct_quote()`
- `fetch_volume_ratio_candidate()`
- `derive_five_day_volume_ratio()`
- `build_volume_ratio_block()`

## 二、任务卡与硬性验收口径

### P2-1：同日快照必须先通过 OHLC 绑定

腾讯 direct `qt` 快照或腾讯 K 线响应内嵌 `qt` 快照，只有同时满足以下条件时，才可以进入 same-day snapshot 路径：

1. `source_date` 等于目标交易日；
2. 快照已收盘；
3. `volume_ratio` 存在且可用；
4. `open / high / low / close` 四个字段在历史目标日行情与快照两侧都完整；
5. 四个字段逐项在规定容差内一致。

任一条件不满足时：

- 不得使用 `same_day_snapshot_plus_sohu_five_day_cross_check`；
- 不得输出成功的 `snapshot_ohlc_check`；
- direct 快照和内嵌 `qt` 快照适用同一规则；
- 若腾讯与搜狐的历史五日成交量推导值仍一致，可降级为 `historical_five_day_volume_cross_check` 并保持 `confirmed`；
- 若历史双源冲突，只能是 `conflict`，不得写入 `confirmed_value`；
- 若只有一个历史来源，只能是 `candidate`，不得自动确认。

原 2026-07-14 正常路径应保持：OHLC 全部匹配时，量比 `1.49` 仍为 `confirmed`。

### P2-2：OHLC matcher 必须 fail-closed

`_quote_values_match()` 的默认 required fields 必须明确为：

- `open`
- `high`
- `low`
- `close`

对 required fields：

- 任一侧任一字段为 `None`、空值或不可解析值，应立即返回 `False`；
- 任一字段超出容差，应返回 `False`；
- 只有四个字段全部存在且逐项匹配，才返回 `True`；
- 调用方不得通过部分字段匹配绕过上述约束。

## 三、请 Fable 必须逐项回答的问题

### A. 快照使用边界

1. 当前实现是否保证 direct `qt` 与内嵌 `qt` 都必须先通过同日、已收盘、量比存在、完整 OHLC 匹配，才可能进入 same-day snapshot 方法？请沿实际数据流证明，不要只看函数名。
2. direct 快照不合格后，变量复用、fallback 顺序或后续分支中，是否仍有机会误用该快照的 `volume_ratio`、`amount`、`turnover_rate` 或 `pct_change`？
3. direct 快照不合格但内嵌快照合格时，当前选择内嵌快照的行为是否与任务卡一致？两者都不合格时，是否一定离开 same-day 路径？
4. 历史日期请求是否仍可能复用最新交易日快照，造成跨日串值？请检查 `source_date`、`is_closed` 与 fallback 的组合，而不只检查单一条件。

### B. 历史双源降级

5. 快照 OHLC 缺失或不匹配后，如果腾讯和搜狐历史成交量推导一致，当前实现是否确实输出：
   - `method = historical_five_day_volume_cross_check`
   - `verification_status = confirmed`
   - `confirmed_by = automation_cross_check`
   - 来源与 cross-check 证据均指向历史推导，而不是快照？
6. 历史双源冲突、历史单源可用、五个前序交易日不足、目标日重复、窗口内日期重复时，是否都不会误报 `confirmed`？
7. `candidate_value` 取搜狐推导、`cross_check.value` 取腾讯推导的方向是否稳定、可解释？容差 `0.01` 是否在边界值及浮点误差下仍符合预期？

### C. OHLC fail-closed

8. `_quote_values_match()` 是否在 left 或 right 任一侧缺少四个 required fields 中任意一个时都返回 `False`？现有测试是否只覆盖了某一侧或某几个字段？
9. 空字符串、非数字字符串、布尔值、`NaN`、正负 `Inf` 等输入，是否可能被 `float()` 接受后绕过 `abs(delta) > tolerance`，从而意外返回 `True`？如果会，请将其视为 fail-closed 缺口并给出最小复现。
10. 是否存在任何调用方传入自定义 `fields` 子集、空 tuple 或异常 tolerance，从而绕开默认四字段约束？如果当前没有，请说明未来接口是否仍暴露了这一风险。
11. OHLC 容差 `0.02` 的等号边界是否符合任务口径？不同价格精度、浮点表示和缺失值转换是否会产生误判？

### D. 证据与状态语义

12. `snapshot_ohlc_check` 是否只会在 OHLC 真正匹配时出现？快照失败后完全不保留 rejected/mismatch 证据，会不会让审计链无法解释为何降级；这是需求允许的简化，还是应该保留非成功证据但明确标记？
13. `source`、`method`、`verification_status`、`confirmed_by`、`cross_check`、`snapshot_ohlc_check` 与最终 `confirmed_value` 是否可能互相矛盾？请特别检查从 candidate 合并进 `build_volume_ratio_block()` 的过程。
14. 网络错误、日期不匹配和 OHLC 冲突被历史双源成功恢复时，原错误是否需要保留；当前实现是否会造成“结果正确但审计证据丢失”？这不是必然 blocker，请按影响定级。

### E. 测试充分性与回归风险

15. 现有测试是否真正覆盖任务卡矩阵，而不是只覆盖 happy path：
   - direct 快照 OHLC 不匹配；
   - 内嵌快照 OHLC 不匹配；
   - 快照 OHLC 缺字段；
   - OHLC 完整匹配且 07-14 仍确认 `1.49`；
   - 历史双源一致、冲突、单源；
   - left/right 两侧分别缺少 `open/high/low/close`；
   - 不可解析值与非有限浮点数。
16. `_quote_values_match()` 同时服务快照校验和腾讯/搜狐行情补全。此次 fail-closed 修改是否会意外阻断合法的 `amount`、`turnover_rate` 或 `pct_change` 补全？现有回归测试能否证明影响可控？
17. 请指出任何“测试会通过，但真实接口 payload 仍可能触发错误 confirmed”的输入形态，并给出最小新增测试建议。

## 四、当前本地验证证据

已执行并通过：

```bash
python3 -m py_compile tools/generate_daily_facts.py tests/test_generate_daily_facts.py
PYTHONPATH=. python3 -m unittest tests.test_generate_daily_facts -v
git diff --check -- tools/generate_daily_facts.py tests/test_generate_daily_facts.py
```

当前单测结果：`Ran 69 tests ... OK`。

测试通过不是封箱结论。请仍以代码路径、状态语义和反例为准。

## 五、请按此格式输出

先给一句结论：

- `可封箱`
- `有非阻断项，可封箱`
- `不可封箱`

然后只列有证据的 findings，按严重度从高到低排列：

```text
[P1/P2/P3] 标题
- 文件与行号：
- 触发条件：
- 实际错误行为：
- 为什么违反任务卡：
- 最小复现或建议补测：
- 最小修复方向：
```

严重度口径：

- `P1`：可能产生错误 `confirmed`、跨日串值或覆盖人工确认；阻断封箱。
- `P2`：fail-closed、证据链或关键回退存在实质缺口；通常阻断封箱。
- `P3`：测试、可审计性或维护性不足，但不改变当前主要结果。

若没有 findings，请明确写：`未发现 P1/P2/P3 问题`，并简要说明你验证过的反例路径。不要为了凑数输出纯风格建议。
