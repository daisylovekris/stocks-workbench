# 股票小工坊 Phase 1 自动化任务卡｜给 GPT 股票窗

> 目标：把股票小工坊里最容易重复出错、最耗人工、最适合脚本化的部分先做稳。
>
> 原则：先替掉事实核对和口径检查，不急着自动写完整复盘，更不碰自动交易。

## 一、这份任务卡的来源

这份任务卡综合了两轮意见：

1. GPT 总控室的建议。
2. Fable 提供的两份施工草案，以及后续判断修正。

最终结论：

- 这两份施工草案都很有料，可以作为 Phase 1 的草案来源。
- 但不能原样照单施工。
- Phase 1 应该先做低误杀、纯本地、可版本化的基础工具。
- `validate_review_chain.py` 先做文本口径 lint 和低误杀检查；严肃的 `facts pack` → 复盘数字一致性核验，以及完整卡片自动更新，等行情事实包格式跑通后再纳入第二步。

## 二、任务合约

### 1. Status

`draft`

### 2. Plan

Phase 1 先做低误杀、纯本地、可版本化的基础工具，先替掉事实核对和口径检查。

### 3. Task Profile

- 任务类型：自动化施工
- 任务范围：lint、封箱、关键位身份判定、行情事实接入前的基础工具
- 任务边界：不碰自动交易，不自动写完整复盘

### 4. Owner

GPT 股票窗 / Codex 施工协作

### 5. Capability ID

`stocks-phase1-automation`

### 6. Review File

建议后续使用：

- `reports/validation/phase1_review.md`

### 7. Notes File

建议后续使用：

- `logs/phase1_notes.md`

### 8. Stop Conditions

出现以下任一情况应先停：

- 规则误杀明显高于预期
- 当前区和历史区无法稳定区分
- `seal_check.py` 开始误伤无关未暂存改动
- 关键位身份输出明显不稳
- 任务开始扩展到 Phase 2 内容

### 9. Falsifier

以下情形说明 Phase 1 施工失败或需要重构：

- lint 不能稳定拦截当前区旧口径
- `derive_level_status.py` 不能稳定区分盘中突破 / 收盘站上 / 连续维持
- `seal_check.py` 不能稳定识别本次封箱相关半状态
- `fetch_daily_quote.py` 还没接上就开始写复盘生成器
- 任务卡开始变成大而全的说明书

### 10. Allowed Paths

Phase 1 建议只碰以下路径：

- `rules/`
- `config/`
- `tools/`
- `reports/validation/`
- `logs/`
- `data/daily/`

其中：

- `rules/`、`config/`、`tools/` 是 Phase 1 主施工区
- `reports/validation/`、`logs/`、`data/daily/` 是输出区
- 正式复盘主文件默认不直接改，除非已经进入明确的生成阶段

### 11. Workflow Inventory

Phase 1 的最小工作流：

1. 读任务卡
2. 写 lint 规则引擎
3. 写封箱检查
4. 写关键位身份判定
5. 跑本地样例
6. 输出校验报告
7. 再决定是否接行情源

### 12. Exit Criteria

Phase 1 完成的最低标准：

- `validate_review_chain.py` 能稳定跑现有复盘并报错
- `seal_check.py` 能稳定检查本次封箱相关文件状态
- `derive_level_status.py` 能从配置 + OHLC 输出价位身份
- 目录和产物路径已经定死
- 规则、脚本、输出三者能互相对上

### 13. Rollback Point

如果出现以下问题，应回滚到只读审查阶段：

- 规则设计过于复杂
- 误报率过高
- 当前区识别不稳定
- 产物目录和脚本职责互相串线
- 实现开始扩张到 Phase 2

## 三、Phase 1 的核心目标

Phase 1 先做三件事：

1. `validate_review_chain.py`
2. `seal_check.py`
3. `derive_level_status.py`

其中：

- `validate_review_chain.py` 先做成可执行 lint，优先扫禁语、动作化表达、旧口径残留、当前区没同步。
- `seal_check.py` 先做成封箱检查，不急着第一天强上 hook。
- `derive_level_status.py` 先做关键位身份判定，把人工口径变成脚本输出。

`fetch_daily_quote.py` 可以作为 Phase 1 的第四个脚本，但这里指的是“正式行情源 / 完整 facts pack 生成器”的后续演进，不是倒退或搁置已经完成的最小事实包能力。

当前已完成的前置成果：

- `tools/akshare_daily_quote_check_v0.1.py` 已完成 `2026-07-06` 最小 facts JSON 试跑，现冻结为同花顺人工基准校准 / 回归工具。
- `data/daily/300274_2026-07-06_facts.json` 已完成一次正式试跑并进入 07-06 复盘链路。
- `tools/generate_daily_facts.py` 已承接正式多日期 facts pack 生成；后续行情源、字段和确认规则统一扩展该脚本，不再让 legacy quote check 承接每日抓取。

## 四、总控室建议的保留部分

总控室的建议里，以下内容应该保留：

### 1. 目录规划

建议先把目录落点定死，避免脚本乱放：

- `data/daily/` 放 `facts pack`
- `config/` 放关键位配置
- `tools/` 放脚本
- `reports/validation/` 放校验报告
- `logs/` 放运行日志

### 2. 风险等级

建议统一定义全局风险等级：

- `P0`：会导致错误交易倾向、自动动作、事实伪造
- `P1`：会导致复盘结论错位、关键位身份错误
- `P2`：旧口径残留、当前区未同步、轻度表述越界
- `P3`：格式、索引、引用、标题类问题

### 3. Phase 1 单独任务卡

不要让 Codex 从整篇蓝图里自由发挥。
Phase 1 应该另起任务卡，只放以下内容：

- 输入
- 输出
- 禁止项
- 验收标准
- 目录落点
- 当前只做什么
- 当前不做什么

## 五、Fable 施工草案中值得保留的部分

### 1. `validate_review_chain.py` 的四组规则拆分

Fable 的 A/B/C/D 四组拆分方向是对的：

- A 组：禁语与口径类
- B 组：动作化表达类
- C 组：结构完整性类
- D 组：文件与链路类

这套拆分适合作为第一版 lint 的框架。

### 2. `config/lint_rules.yaml` 的设计

规则放 YAML，代码只做引擎，这是非常好的方向。

这样以后：

- 改禁语
- 改严重级别
- 改白名单
- 改匹配逻辑

都不需要改 Python 主逻辑。

### 3. `config/300274_levels.yaml` + `derive_level_status.py`

人工维护静态关键位配置，脚本按日推导身份，这个拆分是对的。

这样可以避免：

- 关键位说明文档变成手工同步负担
- 价位身份写成静态说明
- 每天复盘要重新人工判断同一批关键位

## 六、Fable 施工草案中需要修正的地方

### 1. 数字一致性不要写死成统一 `±0` 容差

`facts pack` 数字核验应该按字段类型处理，而不是所有字段都用同一种误差框。

建议思路：

- 价格类：小容差
- 成交额类：按单位换算后比对
- 量比类：允许 `unknown` / `needs_manual_check` / `candidate`

### 2. 固定标题集合要按文件类型区分

不能把所有文件都强制套同一个标题模板。

应按文件类型分别检查：

- 日复盘
- 周观察
- 持仓卡
- 风险卡
- 估值卡
- 加仓分析卡

### 3. `if/若/条件` 不能自动视为安全

“同句出现如果/若/条件”不代表口径就安全。

像“如果明天站上就加仓”这种句子，仍然太动作化。
第一版里，`B2` 这类规则只能做弱提示，不能当安全证明。

### 4. 同一价位身份冲突要限定范围

不能全文件一把扫，看到“跌破”和“站上”就判冲突。

必须限定在：

- 当前日期小节
- 当前判断区
- 当前事实包对应的交易日

### 5. `levels.yaml` 数值必须由股票窗最后核对

Fable 从上下文抽出来的 150 / 145 / 138.61 / 127.30 / 127.18 / 126.10 只能当草案。

正式配置必须由股票窗按以下来源核对：

- 已封箱复盘
- 持仓卡
- 风险卡
- 估值卡
- 低位观察卡

### 6. `pre-commit hook` 第一版不建议硬上

第一阶段建议先：

- 手动跑
- 输出校验报告
- 必要时再接 CI 或本地 hook

原因是：

- 误报率未必稳定
- 多线工作区可能被无关脏状态误伤
- 先把规则跑顺，再把它变成强制闸门更稳

## 七、Phase 1 的建议实现顺序

### Week 1

先做：

- `validate_review_chain.py`
- `seal_check.py`

目标：

- 纯本地
- 零外部依赖
- 先对现有文件做体检

### Week 2

再做：

- `config/300274_levels.yaml`
- `derive_level_status.py`

目标：

- 先用少量人工喂入的 OHLC 验证规则
- 先跑通关键位身份输出

### Week 3

再接：

- `fetch_daily_quote.py`

目标：

- 继续正式化 `tools/generate_daily_facts.py` 的多日期 facts pack 生成链路
- 保留 `tools/akshare_daily_quote_check_v0.1.py` 作为 `2026-07-06` 冻结基准回归样本，不滚动更新其人工基准
- 在正式生成器上继续补齐稳定性和字段证据链
- 接上更完整的行情源 / 配置化 benchmark / 缺失字段管理
- 注意：最小 facts JSON 与多日期正式生成器均已落地；Week 3 的含义是继续扩展 `generate_daily_facts.py`，不是从 legacy 校准脚本另起第二条生产主链。

## 八、Phase 1 的建议目录

建议在开工前先定目录：

- `data/daily/`
  - 每日 `facts pack`
  - 每日 `levels` 输出
- `config/`
  - 关键位配置
  - lint 规则
- `tools/`
  - Python 脚本
- `reports/validation/`
  - 校验报告
- `logs/`
  - 运行日志

## 九、Phase 1 的验收标准

### `validate_review_chain.py`

验收标准：

- 能对存量复盘文件跑 lint
- 能报出禁语、动作化表达、旧口径残留、当前区滞后
- 输出带规则 ID、级别、文件名、行号、命中文本
- 误杀率可控

### `seal_check.py`

验收标准：

- 能检查 git 工作区状态
- 能发现未暂存、半状态、遗漏文件
- 能输出封箱结果
- 第一版不必强制 hook，但结果必须可读

### `derive_level_status.py`

验收标准：

- 输入关键位配置 + 当日 OHLC + 历史序列
- 输出价位身份文本
- 能区分盘中触及、盘中突破、收盘站上、收盘跌破、连续维持
- 不把静态描述写成动态结论

### `fetch_daily_quote.py`

验收标准：

- 能稳定抓到当日行情事实
- 能生成事实包
- 缺失字段能显式标记
- 不把不确定字段硬填成真值

## 十、Phase 1 的禁止项

第一阶段不要做：

- 自动交易
- 自动下单
- 自动买卖建议
- 自动把风险缓和写成风险解除
- 自动把盘中突破写成收盘站上
- 自动把观察条件写成执行动作
- 自动让 LLM 自由编造事实
- 直接上重型研究平台

## 十一、Phase 1 的最终口径

Phase 1 不是“自动写完整复盘”，而是先把最容易出错的部分工具化：

- 禁语检查
- 口径检查
- 关键位身份判定
- 封箱检查

等这四件事稳了，再往下接：

- `facts pack`
- 自动复盘生成
- 周观察生成
- 消息面聚合
- 预测参考层

## 十二、给 GPT 股票窗的最终一句话

> 先做低误杀、纯本地、可版本化的 Phase 1：lint、封箱、关键位身份；
> 最小 facts JSON 已完成试跑；
> 后续行情源 / facts pack 正式化应承接现有 quote check 脚本；
> `facts pack` 数字核验和完整卡片自动更新放在后续步骤逐步接入。
