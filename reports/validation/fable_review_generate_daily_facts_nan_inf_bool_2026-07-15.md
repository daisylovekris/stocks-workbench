# Fable 二审归档：generate_daily_facts.py NaN / Inf / bool 加固

- 审查对象：tools/generate_daily_facts.py
- 测试对象：tests/test_generate_daily_facts.py
- 审查日期：2026-07-15
- 审查性质：只读二审

复核完成。实际源码（tools/generate_daily_facts.py:426-444）、测试（tests/test_generate_daily_facts.py:198-225）与最小材料完全一致，且我独立复跑了三个 _quote_values_match 定向测试（含旧有回归），全部通过。

结论

可封箱

五项核对

1. 非有限值

通过。

检查顺序为：

bool 拦截 → to_float_or_none → None 拦截 → math.isfinite 拦截 → 容差比较

NaN / +Inf / -Inf 无论出现在左侧、右侧还是两侧，都在到达：

abs(...) > tolerance

之前被 isfinite 拒绝，消除了旧逻辑中：

abs(nan - x) > tol

恒为 False 导致的误匹配路径。

额外收益：to_float 会把字符串 "nan" / "inf" 解析为浮点数，同样被后置的 isfinite 拦住，字符串形态的非有限值也是 fail-closed。

2. 布尔值

通过。

isinstance(left.get(field), bool) or isinstance(right.get(field), bool)

位于任何数值转换之前。

由于 Python 中 bool 是 int 子类：

float(True) == 1.0

前置拦截是唯一正确的位置，当前实现正是如此，且左右两侧对称覆盖。

3. 容差语义

保持原状。

有限数路径仍是严格大于比较：

> tolerance

默认容差为 0.02。

新增的两个检查对有限数均为透明。

旧有测试：

test_quote_values_match_requires_complete_ohlc

复跑通过，确认原语义未被扰动。

新测试用 1.019 / 1.021 验证容差内外，数值离 0.02 边界有安全余量，不受浮点表示误差影响。

4. 测试覆盖

充分。

所列 8 类场景全部落实：

* 左侧 NaN
* 右侧 NaN
* 左侧 +Inf
* 右侧 +Inf
* 左侧 -Inf
* 右侧 -Inf
* 双侧 NaN
* 双侧同号 Inf
    * +Inf 一条
    * -Inf 一条
* 左侧布尔值
* 右侧布尔值
* 容差内有限值
* 容差外有限值

布尔值与非有限值合计覆盖 11 个 subTest。

其中“双侧 NaN”和“双侧同号 Inf”正是旧逻辑最危险的误匹配路径，已有直接回归。

测试经我独立复跑确认通过，与你报告的 71 / 112 通过口径一致。

5. P1/P2 阻断项

无。

未发现会破坏匹配语义、生产或评审边界、或误导后续任务的问题。

风险说明

未发现阻断性问题。

两个可选的非阻断观察，本轮无需处理：

* 字符串形态 "nan" / "inf" 目前由代码正确拒绝，但测试矩阵未显式覆盖；若未来有人重构 to_float，该防线没有回归保护。属可选加固，非 P2。
* import math 插在 copy 与 json 之间，不符合字母序，纯格式问题。

最终判定

本轮 NaN / Inf / bool 修补实现正确、语义收敛、测试矩阵完整覆盖该漏洞类别，可封箱。

⸻

本轮为只读审查：未修改任何文件；运行的命令仅为 grep / Read 定位源码，以及 python3 -m unittest 复跑三个定向测试。
