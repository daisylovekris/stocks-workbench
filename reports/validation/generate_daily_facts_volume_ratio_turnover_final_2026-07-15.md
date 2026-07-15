# generate_daily_facts 量比与换手率抓取自动化最终验证报告

日期：2026-07-15

## 1. 任务范围

本轮封箱范围包括：

* 量比抓取与核验
* 换手率抓取与核验
* 同日快照 OHLC 绑定
* 五日成交量交易日去重
* 历史双源降级
* NaN / +Inf / -Inf / bool fail-closed 加固

不包含：

* `market_indices`
* `sector_context`
* `disclosure_status`
* `news_policy_context`
* 交易建议或持仓动作

## 2. 关键结果

当前已验证事实：

* 2026-07-13 量比：1.25
* 2026-07-14 量比：1.49
* 2026-07-13 换手率：4.70%
* 2026-07-14 换手率：6.05%

两份 facts pack 仍保持 `partial`：

* `data/daily/300274_2026-07-13_facts.json`
* `data/daily/300274_2026-07-14_facts.json`

原因是四类上下文字段仍需人工或后续自动化补齐：`market_indices`、`sector_context`、`disclosure_status`、`news_policy_context`。本轮不得将其状态改写为完整成功。

## 3. 漏洞修补

`_quote_values_match()` 已完成 fail-closed 加固：

* 在浮点转换前显式拒绝 `bool`，避免 `True` / `False` 被 Python 当作 `1.0` / `0.0` 参与比较。
* 转换后通过 `math.isfinite()` 拒绝非有限数。
* 任意一侧出现 `NaN`、`+Inf` 或 `-Inf` 时立即返回 `False`。
* 正常有限数仍沿用原容差语义：`abs(left_value - right_value) > tolerance` 时才判为不匹配。

## 4. 测试证据

封箱前复跑结果：

* `python3 -m py_compile tools/generate_daily_facts.py tests/test_generate_daily_facts.py tools/akshare_daily_quote_check_v0.1.py tests/test_akshare_daily_quote_check.py`：通过
* `python3 -m unittest discover -s tests -p 'test_generate_daily_facts.py'`：71 tests passed
* `/private/tmp/stocks-gdf-venv/bin/python3 -m pytest -q`：112 passed，22 subtests passed
* `git diff --check`：通过
* Fable 二审：通过
* P1/P2 阻断项：无

## 5. 环境说明

本轮验证环境：

* 系统 Python：`/opt/homebrew/bin/python3`
* Python 版本：3.14.4
* 临时 venv：`/private/tmp/stocks-gdf-venv`
* pytest：9.1.1

仓库当前缺少正式测试依赖声明和固定虚拟环境。`tests/test_validate.py` 依赖 `pytest`，本轮通过临时 venv 补齐后完成全量测试。该事项属于独立工程卫生缺口，不阻断本轮封箱。

## 6. 非阻断观察

Fable 二审提出两个可选的非阻断观察，本轮无需处理：

* 字符串形态 `"nan"` / `"inf"` 目前由代码正确拒绝，但测试矩阵未显式覆盖；若未来有人重构 `to_float`，该防线没有回归保护。属可选加固，非 P2。
* `import math` 插在 `copy` 与 `json` 之间，不符合字母序，纯格式问题。

## 7. 最终结论

量比与换手率抓取自动化、本轮 OHLC 绑定 fail-closed 加固及对应回归测试均已完成验证。Fable 最终二审结论为“可封箱”，未发现 P1/P2 阻断项。
