# 股票小工坊自动化总蓝图｜v0.1

> 这是 `stocks` 仓库的自动化架构工作文档，和 `rules/automation_architecture_v0.1.md` 保持同方向、低误差演进。

## 一、总目标

股票小工坊要做的，不是“自动炒股机器人”，而是一个有闸门的工作台：

- 事实自动化
- 规则拦截
- 叙事生成
- 预测参考

核心原则：

- 不自动交易
- 不把预测当保证
- 不把观察条件写成执行动作
- 不让 LLM 编造行情真值
- 不让人工继续做重复性核对

一句话概括：

> 脚本负责事实，规则负责拦截，LLM 负责叙事，预测只做参考。

## 二、目录与风险

### 1. 目录规划

建议先把目录落点定死，避免脚本乱放：

- `data/daily/` 放 `facts pack`
- `config/` 放关键位配置、lint 规则
- `tools/` 放脚本
- `reports/validation/` 放校验报告
- `logs/` 放运行日志

### 2. 全局风险等级

建议统一定义全局风险等级：

- `P0`：会导致错误交易倾向、自动动作、事实伪造
- `P1`：会导致复盘结论错位、关键位身份错误
- `P2`：旧口径残留、当前区未同步、轻度表述越界
- `P3`：格式、索引、引用、标题类问题

## 三、自动化架构

建议拆成 5 层：

### 1. 采集层

负责抓取：

- 行情
- 公告
- 新闻
- 板块
- 资金面
- 历史样本

### 2. 归一层

负责把输入统一成可用结构：

- 统一字段
- 统一日期
- 统一交易日口径
- 统一关键位状态
- 统一消息分类标签

### 3. 校验层

负责拦截错误：

- 旧口径残留
- 动作化表达
- “硬底 / 支撑 / 风险解除”误写
- git 漏项
- 事实与文本不一致

### 4. 生成层

负责产出文档草稿：

- 每日复盘
- 周观察
- 持仓卡更新
- 风险卡更新
- 估值卡更新
- 股性分析专题

### 5. 输出层

负责最终落盘：

- 自动写 Markdown
- 必要时更新索引
- 必要时生成审计日志
- 可选推送到常用查看位置

## 四、任务编排 / 合约层

这里吸收 `repo-harness` 的工作流骨架，但只保留适合股票小工坊的部分。

建议把任务编排理解为“可执行合约”：

- `contract.template.md` 的思路 → Phase 1 任务卡模板
- `review.template.md` 的思路 → 封箱复核卡模板
- `handoff-protocol.md` 的思路 → 夜班交班模板
- `check-task-workflow.sh` 的思路 → `seal_check.py` 设计参考
- `check-task-sync.sh` 的思路 → 文件改动与任务卡同步检查参考
- worktree 隔离 / bounded task / bounded commit → 未来执行隔离策略参考

这个层主要负责：

- 任务边界
- 停止条件
- 允许路径
- 证据链
- 交接和续接

它不负责行情、不负责叙事，只负责把后面的脚本和文档纳入可控工作流。

## 五、Phase 1 / Phase 1.5 优先级

建议的先后顺序：

1. `validate_review_chain.py`
2. `seal_check.py`
3. `derive_level_status.py`
4. `fetch_daily_quote.py`
5. `fact_verification_worker_v0.1.md`

### Fact Verification Worker 的位置

- 位于 `fetch_daily_quote` / AkShare 主抓取之后
- 位于 review generation / validator 之前
- 负责字段级第二来源 verification
- 不直接改主 facts
- 只输出 verification 状态供 merge / validator 使用

详细设计见：`automation/fact_verification_worker_v0.1.md`

## 六、facts pack 和 levels.json 要分离

这是我们特别认同的一点。

### 1. `facts pack`

建议作为每日事实快照保存，例如：

- `data/daily/300274_YYYY-MM-DD_facts.json`

建议包含：

- `schema_version`
- `generated_at`
- 当日行情字段
- 公告状态
- 新闻状态
- 板块和大盘背景
- 量比候选来源
- 缺失字段显式标记为 `unknown` / `needs_manual_check`

原则：

- 不要强行填满空字段
- 不要假装今天没有缺失

建议为需要人工或多源确认的字段统一加入 `verification` 结构。

### 2. `levels.json`

不要把它做成静态说明文档，而要做成每日动态身份结果。

建议结构分成两层：

- `config/300274_levels.yaml`
  - 人工维护的关键位配置
  - 禁写规则
