# GitHub Stars 股票/金融相关仓库筛选报告

- **来源：** github-stars-full-2026-05-31.md（257 个仓库）
- **筛选日期：** 2026-06-01
- **筛选结果：** 14 个相关仓库（12 个已标记"股票金融" + 2 个关键词命中）

---

## 筛选结果

### 第一类：立刻可用于股票小工坊

---

#### 1. ZhuLinsen/daily_stock_analysis

- **repo name：** ZhuLinsen/daily_stock_analysis
- **URL：** https://github.com/ZhuLinsen/daily_stock_analysis
- **description：** LLM驱动的 A/H/美股智能分析：多数据源行情 + 实时新闻 + LLM决策仪表盘 + 多渠道推送，零成本定时运行，纯白嫖
- **language：** Python
- **stars：** 39,498
- **初步分类：** 股票金融
- **对股票小工坊的用途：** 直接对标小工坊需求——A股行情 + LLM 分析 + 多渠道推送。可作为每日持仓提醒的参考实现，甚至直接复用其推送管道
- **风险点：** 依赖 LLM API（可能需要 OpenAI 或其他 key）；数据源可能依赖 akshare；高 star 项目但需确认最近维护状态
- **优先级：** **P0**

---

#### 2. IvanWng97/TradingAgents-Telegram

- **repo name：** IvanWng97/TradingAgents-Telegram
- **URL：** https://github.com/IvanWng97/TradingAgents-Telegram
- **description：** Telegram bot wrapping TradingAgents — chat-driven watchlist with parallel multi-ticker analysis, cancellation, and Telegraph reports
- **language：** Python
- **stars：** 43
- **初步分类：** 股票金融
- **对股票小工坊的用途：** 直接适配 Telegram 接口，可做持仓多股并行分析 + Telegram 推送。与小工坊"每日持仓提醒"需求高度匹配
- **风险点：** star 数低（43），代码质量待验证；依赖 TradingAgents 主项目；可能需要 Telegram Bot Token
- **优先级：** **P0**

---

#### 3. mingli30119/stock-analysis

- **repo name：** mingli30119/stock-analysis
- **URL：** https://github.com/mingli30119/stock-analysis
- **description：** 一句话搞定个股分析
- **language：** Python
- **stars：** 482
- **初步分类：** 股票金融
- **对股票小工坊的用途：** 已完成 Phase 1 试跑，数据采集能力验证通过。可继续作为小工坊的数据采集底层
- **风险点：** akshare 接口稳定性；部分数据块失败（分红、机构评级）；Phase 2/3 需要 Claude Code Skill
- **优先级：** **P1**（已在使用中）

---

### 第二类：值得只读研究

---

#### 4. virattt/dexter

- **repo name：** virattt/dexter
- **URL：** https://github.com/virattt/dexter
- **description：** An autonomous agent for deep financial research
- **language：** TypeScript
- **stars：** 26,687
- **初步分类：** 股票金融
- **对股票小工坊的用途：** 自主金融研究 agent，可参考其研究框架和数据源整合方式。适合学习"如何让 AI 做深度个股研究"
- **风险点：** TypeScript 栈，与小工坊 Python 生态不直接兼容；高 star 不等于适合 A 股；可能偏美股
- **优先级：** **P1**

---

#### 5. shiyu-coder/Kronos

- **repo name：** shiyu-coder/Kronos
- **URL：** https://github.com/shiyu-coder/Kronos
- **description：** Kronos: A Foundation Model for the Language of Financial Markets
- **language：** Python
- **stars：** 27,575
- **初步分类：** 股票金融
- **对股票小工坊的用途：** 金融市场基础模型，可参考其对市场"语言"的理解方式。适合长期研究，不适合短期接入
- **风险点：** 学术项目，部署复杂度高；需要 GPU 资源；不直接产出交易信号
- **优先级：** **P2**

---

#### 6. anthropics/financial-services

- **repo name：** anthropics/financial-services
- **URL：** https://github.com/anthropics/financial-services
- **description：** （Anthropic 官方金融服务参考）
- **language：** Python
- **stars：** 28,845
- **初步分类：** 股票金融
- **对股票小工坊的用途：** Anthropic 官方的金融行业参考实现，可学习 Claude 在金融分析中的最佳实践。适合只读研究
- **风险点：** 参考性质，非直接可用工具；可能偏企业级场景
- **优先级：** **P1**

---

### 第三类：适合后续接入 Telegram / 每日提醒

---

#### 7. leiting-eric/DailyBrief

- **repo name：** leiting-eric/DailyBrief
- **URL：** https://github.com/leiting-eric/DailyBrief
- **description：** AI 每日新闻简报 · GitHub 热门 + X 热门文章 + 行情技术分析 · 23 个数据源聚合 + LLM 中文摘要 · 本地或 GitHub Actions 部署
- **language：** TypeScript
- **stars：** 206
- **初步分类：** 不确定（但含行情技术分析能力）
- **对股票小工坊的用途：** 已有"行情技术分析"模块 + GitHub Actions 定时部署能力，可参考其定时推送架构
- **风险点：** 主要功能是新闻聚合，股票分析可能只是附带；TypeScript 栈
- **优先级：** **P2**

---

#### 8. 6551Team/opennews-mcp

- **repo name：** 6551Team/opennews-mcp
- **URL：** https://github.com/6551Team/opennews-mcp
- **description：** News Aggregation · AI Ratings · Trading Signals · Real-time Updates
- **language：** Python
- **stars：** 1,384
- **初步分类：** 股票金融
- **对股票小工坊的用途：** 新闻聚合 + AI 评级 + 交易信号，可作为小工坊的新闻/信号输入源。MCP 协议适配 Claude Code
- **风险点：** "Trading Signals" 需要谨慎评估，避免自动交易风险；数据源质量待验证
- **优先级：** **P1**

---

### 第四类：技术指标 / 回测工具

---

#### 9. cinar/indicator

- **repo name：** cinar/indicator
- **URL：** https://github.com/cinar/indicator
- **description：** Indicator Go delivers a rich set of technical analysis indicators, customizable strategies, and a powerful backtesting framework. No dependencies, just pure simplicity
- **language：** Go
- **stars：** 1,124
- **初步分类：** 不确定（实为技术指标库）
- **对股票小工坊的用途：** 技术指标计算 + 回测框架，可补充小工坊缺失的技术面分析能力。Go 语言但无外部依赖
- **风险点：** Go 语言，与 Python 生态不直接兼容；需要自行封装接口；不直接提供 A 股数据
- **优先级：** **P2**

---

#### 10. brokermr810/QuantDinger

- **repo name：** brokermr810/QuantDinger
- **URL：** https://github.com/brokermr810/QuantDinger
- **description：** AI quantitative trading platform for crypto, stocks, and forex with backtesting, live trading, market data, and multi-agent research
- **language：** Python
- **stars：** 6,968
- **初步分类：** 股票金融
- **对股票小工坊的用途：** AI 量化平台，含回测 + 实盘 + 多 agent 研究。可参考其回测框架和多 agent 架构
- **风险点：** 含"live trading"能力，**严禁接入实盘交易**；覆盖 crypto/forex，A 股支持度待验证；功能复杂，学习成本高
- **优先级：** **P2**

---

### 第五类：暂时不建议碰

---

#### 11. moss-site/moss-trade-bot-skills

- **repo name：** moss-site/moss-trade-bot-skills
- **URL：** https://github.com/moss-site/moss-trade-bot-skills
- **description：** LLM-powered trading agents that turn plain natural language into a five-pillar strategy: Trend, Mean-Reversion, Momentum, Volume, and Risk. Each strategy is hosted, self-evolving, configurable
- **language：** Python
- **stars：** 142
- **初步分类：** 股票金融
- **对股票小工坊的用途：** LLM 交易 agent，理论上可参考其策略框架
- **风险点：** star 数低，成熟度存疑；"self-evolving"策略 + "configurable"暗示可能自动执行交易；与"不做自动交易"原则冲突
- **优先级：** **P3**

---

#### 12. Open-Dev-Society/OpenStock

- **repo name：** Open-Dev-Society/OpenStock
- **URL：** https://github.com/Open-Dev-Society/OpenStock
- **description：** OpenStock is an open-source alternative to expensive market platforms. Track real-time prices, set personalized alerts, and explore detailed company insights
- **language：** TypeScript
- **stars：** 12,805
- **初步分类：** 股票金融
- **对股票小工坊的用途：** 开源市场平台，功能包括实时价格追踪和提醒。理论上可参考其提醒架构
- **风险点：** TypeScript 全栈，与小工坊 Python 生态差异大；12K star 但需确认是否支持 A 股；部署复杂
- **优先级：** **P3**

---

### 第六类：只做灵感参考

---

#### 13. bwjoke/fomo5000.com

- **repo name：** bwjoke/fomo5000.com
- **URL：** https://github.com/bwjoke/fomo5000.com
- **description：** AI market map for scanning 5,000+ U.S.-listed stocks
- **language：** JavaScript
- **stars：** 79
- **初步分类：** 股票金融
- **对股票小工坊的用途：** 美股市场地图可视化，可参考其扫描和可视化思路
- **风险点：** 仅限美股；star 低；JavaScript 栈；对 A 股无直接价值
- **优先级：** **P3**

---

#### 14. jnMetaCode/agency-agents-zh

- **repo name：** jnMetaCode/agency-agents-zh
- **URL：** https://github.com/jnMetaCode/agency-agents-zh
- **description：** 211 个即插即用的 AI 专家角色，覆盖金融等 18 个部门。含 46 个中国市场原创智能体
- **language：** Shell
- **stars：** 13,371
- **初步分类：** 股票金融
- **对股票小工坊的用途：** 可参考其金融相关 agent 角色定义，学习如何给 Claude Code 设定金融分析角色
- **风险点：** 通用 agent 角色库，非专门金融工具；Shell 脚本为主；金融角色质量待验证
- **优先级：** **P3**

---

## 推荐路线

### 第一批先审查哪 3 个

1. **ZhuLinsen/daily_stock_analysis**（P0）— 39K star，A/H/美股 LLM 分析 + 多渠道推送，最直接对标小工坊需求
2. **IvanWng97/TradingAgents-Telegram**（P0）— Telegram bot 多股并行分析，直接适配"每日持仓提醒"场景
3. **6551Team/opennews-mcp**（P1）— 新闻聚合 + AI 评级 + MCP 协议，可作为小工坊的新闻/信号输入源

### 哪个适合辅助阳光电源分析

- **ZhuLinsen/daily_stock_analysis** — 如果支持 A 股个股深度分析，可直接用于阳光电源的每日追踪
- **virattt/dexter** — 自主金融研究 agent，可参考其研究框架来增强阳光电源的分析深度

### 哪个适合补技术指标

- **cinar/indicator**（P2）— Go 语言技术指标库，无依赖，可参考其指标计算逻辑。但需要自行用 Python 封装
- 备选：akshare 本身已提供部分技术指标接口，不一定需要额外引入

### 哪个适合做每日持仓提醒

- **IvanWng97/TradingAgents-Telegram**（P0）— 最直接匹配，Telegram bot + 多股并行分析
- **ZhuLinsen/daily_stock_analysis**（P0）— 多渠道推送能力（可能含 Telegram），39K star 成熟度更高
- **leiting-eric/DailyBrief**（P2）— GitHub Actions 定时部署，可参考其自动化流程

### 哪些暂时封印，不要跑

- **moss-site/moss-trade-bot-skills** — star 低 + 自动交易风险
- **brokermr810/QuantDinger** — 含 live trading 能力，严禁接入实盘，仅可只读研究回测部分
- **Open-Dev-Society/OpenStock** — TypeScript 全栈，改造成本高
- **bwjoke/fomo5000.com** — 仅美股，对 A 股无价值
- **shiyu-coder/Kronos** — 学术项目，部署复杂，需 GPU
