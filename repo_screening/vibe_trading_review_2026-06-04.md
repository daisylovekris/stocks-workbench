# HKUDS/Vibe-Trading 只读可用性评估｜2026-06-04

> 评估范围：只读公开 README 与项目结构，不 clone、不安装、不运行。
> 评估目标：判断该工具对股票小工坊的可用性与借鉴价值。
> 评估时间：2026-06-04

---

## 一、核心功能

Vibe-Trading 是香港大学数据科学实验室（HKUDS）开源的金融研究工作台，核心定位是：

- 自然语言 → 金融分析 → 回测 → 报告生成
- 多智能体研究团队（Swarm）
- 跨市场数据接入与自动回测
- 持久化研究记忆（Research Goal / Hypothesis Registry）
- 影子账户（Shadow Account）行为诊断
- 可选的券商交易连接（实验性）

四根支柱：

1. 自我改进的交易智能体（自然语言研究、策略草拟、记忆驱动工作流）
2. 多智能体团队（投资、量化、加密、风控，29 个预设团队）
3. 跨市场数据与回测（A 股/港/美/加密/期货/外汇，7 个数据源自动回退）
4. 影子账户（券商交易日志行为诊断）

---

## 二、A 股数据支持

A 股支持是该项目最强的板块之一：

| 数据源 | 特点 | 是否需要 Key |
|--------|------|-------------|
| **mootdx** | 通达信原生 TCP 协议，日线/分钟线，无 Token，无 IP 限制 | 不需要 |
| **AKShare** | 最广泛覆盖（A 股/港股/美股/期货/外汇/ETF），免费 | 不需要 |
| **Tushare** | 提供时点基本面数据（营收、利润、ROE 等），最完整 | 需要 Token |
| **Futu** | 富途证券，A 股+港股 | 不需要（只读） |

自动回退链：Tushare → mootdx → AKShare，全部市场无需任何 API Key 即可工作。

---

## 三、数据源定位

| 数据源 | 在股票小工坊中的定位 |
|--------|---------------------|
| **mootdx** | 当前小工坊用 akshare 采集，mootdx 可作为 A 股行情备用源，尤其适合分钟线和历史日线 |
| **akshare** | 小工坊已在用，Vibe-Trading 的 akshare skill 可以参考其路由逻辑 |
| **tushare** | 若有 Token，可补充基本面数据（营收/利润/ROE），小工坊目前缺这块 |
| **yfinance** | 小工坊暂不需要港股/美股数据，但未来扩展可用 |

---

## 四、是否能只用于研究而不启用交易？

**可以。**

交易功能是完全可选的：

- 券商 Connector 需要单独配置，默认不启用
- 研究、回测、因子分析、技术指标、Swarm 团队等功能不依赖交易模块
- MCP 工具中交易相关工具（`trading_*`）需要配置 Connector 才有意义
- Shadow Account 只是分析券商导出的交易日志，不涉及下单

**结论：** 可以只用研究/回测/数据/技能模块，完全不碰交易功能。

---

## 五、Research Goal / Evidence / Claim 机制借鉴

这是该项目对小工坊最有借鉴价值的部分：

### 机制

- **Research Goal：** 任务级研究目标，持久化存储 claim、验收标准、evidence 行、预算、完成策略
- **Evidence：** 每次发现/结论作为一条 evidence 追加到 goal
- **Hypothesis Registry：** 假设注册表，支持创建、更新、关联回测、失效标记

### 对小工坊的借鉴

| 小工坊现有 | Vibe-Trading 做法 | 借鉴价值 |
|-----------|------------------|---------|
| 每日复盘 md | Research Goal + Evidence 行 | 可以把"后续计划"变成结构化的 goal，每条进展作为 evidence |
| 研究目标卡（research_goal） | Goal 生命周期管理（创建/继续/编辑/取消/完成） | 小工坊的 research_goal 可以加完成状态和 evidence 追踪 |
| 估值/风险/跟踪卡 | Hypothesis Registry | 可以把"证伪条件"变成假设，每条验证结果作为 evidence |
| 手动复盘 | Agent 自动推进 goal | 不需要自动推进，但结构化 goal 思路值得参考 |

**建议：** 不需要直接用它的系统，但可以借鉴"goal + evidence + hypothesis"的结构化思路，用于改进小工坊的研究卡和复盘流程。

---

## 六、技术指标、估值、盈利预测、宏观分析相关 Skills

77 个 Skills 分 8 类，以下对小工坊有参考价值：

| Skill | 类别 | 小工坊用途 |
|-------|------|-----------|
| `technical-basic` | 策略 | 基础技术指标（MACD/RSI/均线等） |
| `candlestick` | 策略 | K 线形态识别 |
| `ichimoku` | 策略 | 一目均衡表 |
| `valuation-model` | 分析 | 估值模型参考 |
| `earnings-forecast` | 分析 | 盈利预测参考 |
| `macro-analysis` | 分析 | 宏观分析框架 |
| `dividend-analysis` | 分析 | 分红分析 |
| `factor-research` | 分析 | 因子研究 |
| `ashare-pre-st-filter` | 风险 | A 股 ST 风险筛选 |
| `financial-statement` | 资金流 | 财报分析 |
| `sector-rotation` | 资产类别 | 板块轮动 |

**建议：** 这些 skill 本质是结构化的分析提示词（prompt），值得拆出来学习其分析框架，不需要跑整个系统。

---

## 七、是否必须配置 LLM API Key？

**是的，核心功能需要 LLM。**

| 场景 | 是否需要 LLM |
|------|-------------|
| Agent 对话式研究 | 需要 |
| Swarm 多智能体团队 | 需要 |
| Skill 执行 | 需要（skill 是给 LLM 的结构化 prompt） |
| Research Goal 推进 | 需要 |
| 回测引擎（直接调用） | 不一定需要（可直接用 Python API） |
| 数据加载器（直接调用） | 不需要 |
| Alpha Zoo 因子计算 | 不需要（纯数学公式） |

**支持 13 个 LLM 提供商：** OpenRouter、OpenAI、DeepSeek、Gemini、Groq、通义千问、智谱、月之暗面、MiniMax、小米 MIMO、Z.ai、Ollama（本地免费）、OpenAI Codex（OAuth）。

**默认配置：** DeepSeek + `deepseek-v4-pro`，成本较低。

**Ollama 方案：** 完全本地免费，但模型质量影响 agent 是否真正调用工具。

---

## 八、本地运行复杂度

| 安装方式 | 时间 | 适合场景 |
|---------|------|---------|
| Docker | 2 分钟 | 快速试用 |
| 本地 pip 安装 | 5 分钟 | 开发、完整 CLI |
| MCP 插件 | 3 分钟 | 集成到 Claude Desktop / Cursor |
| ClawHub | 1 分钟 | 一键安装 |

**前置条件：**

- Python 3.11+
- LLM API Key（或 Ollama 本地模型）
- Docker 或 pip 环境

**复杂度评估：**

- Docker 方式最简单，`docker compose up --build` 即可
- 本地安装需要 Python 环境 + venv
- Web UI 需要 Node.js（前端是 React 19 + Vite）
- 整体复杂度中等，比小工坊当前的纯 Markdown + Python 脚本方式重得多

---

## 九、对股票小工坊的用途评估

| 用途 | 可行性 | 建议 |
|------|--------|------|
| **A 股行情备用数据源** | 高 | mootdx 作为 akshare 的备用，无需 Key |
| **技术指标补强** | 高 | technical-basic、candlestick 等 skill 可拆出来参考 |
| **回测框架参考** | 中 | 回测引擎复杂度高，但思路可借鉴（Monte Carlo、Walk-Forward） |
| **Research Goal 结构参考** | 高 | goal + evidence + hypothesis 结构对小工坊改进复盘流程有直接价值 |
| **多市场数据源参考** | 低 | 小工坊当前只做 A 股，暂不需要港/美/加密 |
| **直接跑完整系统** | 中 | 可以 Docker 试跑，但整体较重，与小工坊轻量风格不一致 |

---

## 十、风险点

| 风险 | 等级 | 说明 |
|------|------|------|
| **Broker Connector** | 🔴 高 | 8 个券商连接器（IBKR/Robinhood/Tiger/Longbridge/Alpaca/OKX/Binance/Futu），默认不启用但存在 |
| **模拟盘/实盘下单** | 🔴 高 | 6 个 connector 支持 sandbox 下单，Robinhood 支持 agentic trading，标注"实验性" |
| **API Key 与 OAuth 风险** | 🟡 中 | LLM API Key 存 .env，券商 OAuth 需要授权，必须确保不泄露 |
| **LLM 幻觉风险** | 🟡 中 | 官方明确指出：轻量模型会"凭记忆回答"而非调用工具，需要好模型 |
| **依赖过重** | 🟡 中 | FastAPI + React + LangChain + 多数据源 + 多券商 SDK，依赖链较重 |
| **实验性功能** | 🟡 中 | 交易功能标注"实验性，未经真实券商验证" |
| **Alpha Zoo 准确性** | 🟢 低 | 因子公式来自学术论文和券商研报，有 AST 验证和 lookahead guard |

---

## 十一、结论

**评级：只读参考 + 可选择性试跑数据模块**

理由：

1. **核心价值在研究侧，不在交易侧。** 77 个 skill、Research Goal 机制、Alpha Zoo、回测引擎，对小工坊有参考价值。
2. **A 股数据源值得借鉴。** mootdx 作为 akshare 备用源，自动回退链设计合理。
3. **交易功能是高风险区。** 8 个券商 connector、实验性下单、agentic trading，小工坊不应碰。
4. **整体较重。** 与小工坊当前"纯 Markdown + Python 脚本 + 低依赖"风格不一致，不适合直接集成。
5. **LLM 依赖是硬门槛。** 不配 LLM Key 只能用数据加载器和 Alpha Zoo 计算，无法用 agent 和 skill。

建议态度：

- ✅ 拆出 skill 和 Research Goal 结构学习
- ✅ 参考其 A 股数据源路由逻辑
- ✅ 参考 Alpha Zoo 的因子公式
- ❌ 不启用任何 broker connector
- ❌ 不配置券商 OAuth
- ❌ 不跑模拟盘/实盘下单
- ⚠️ Docker 试跑可以，但只用于数据/回测/因子，不碰交易

---

## 十二、如果后续试跑：只读数据/技术指标方案

**前提：** 只用于数据读取和技术指标计算，不启用任何交易功能。

### 方案 A：Docker 只跑数据层

```bash
# 1. Clone
git clone https://github.com/HKUDS/Vibe-Trading.git
cd Vibe-Trading

# 2. 只配置数据源，不配置券商
cp .env.example .env
# 编辑 .env，只设置 LLM provider（如 DeepSeek）
# 不配置任何 broker connector
# 不配置 TUSHARE_TOKEN（使用 mootdx + akshare 免费回退）

# 3. Docker 启动
docker compose up --build
```

### 方案 B：Python 直接调用数据加载器

```python
# 只用数据加载器，不跑 agent
# 需要 clone 后 pip install -e .
from agent.backtest.loaders.registry import DataLoaderRegistry

loader = DataLoaderRegistry()
# A 股日线（自动回退：tushare → mootdx → akshare）
df = loader.load("300274.SZ", start="2025-01-01", end="2026-06-04")
```

### 方案 C：Alpha Zoo 因子计算

```bash
# 只跑因子计算，不需要 LLM
vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025
```

### 方案 D：MCP 插件只读集成

```json
// Claude Desktop config，只启用研究工具，不启用交易工具
{
  "mcpServers": {
    "vibe-trading": {
      "command": "vibe-trading-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

**注意：** 即使 MCP 集成，交易工具仍会出现在工具列表中。需要靠自觉不调用，或通过 MCP 权限配置屏蔽。

### 禁止事项

- ❌ 不配置任何券商 connector
- ❌ 不运行 `vibe-trading connector` 相关命令
- ❌ 不调用 `trading_*` MCP 工具
- ❌ 不配置券商 OAuth
- ❌ 不启用 `VIBE_TRADING_ENABLE_SHELL_TOOLS`
- ❌ 不将 .env 文件提交到任何仓库

---

## 附录：项目关键数据

| 项目 | 数据 |
|------|------|
| 仓库 | https://github.com/HKUDS/Vibe-Trading |
| License | MIT |
| 语言 | Python 90%，TypeScript 7% |
| Skills | 77 个，8 类 |
| Swarm 预设 | 29 个 |
| MCP 工具 | 36 个 |
| Alpha 因子 | 452 个（qlib158 + alpha101 + gtja191 + academic） |
| 数据源 | 7 个（tushare/akshare/mootdx/yfinance/OKX/CCXT/Futu） |
| 券商 Connector | 8 个（IBKR/Robinhood/Tiger/Longbridge/Alpaca/OKX/Binance/Futu） |
| LLM 提供商 | 13 个 |
| 安装方式 | Docker / pip / MCP / ClawHub |
