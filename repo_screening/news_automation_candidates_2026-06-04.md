# 盘前消息自动化候选仓库筛选｜2026-06-04

> 来源：github-stars-full-2026-05-31.md（257 个仓库）+ 已有 repo_screening
> 筛选目标：适合股票小工坊"盘前消息自动化 / 财经新闻聚合 / 公司公告监控 / RSS / 新闻去重 / 摘要生成"
> 筛选日期：2026-06-04

---

## 一、筛选标准

### 优先筛选

- RSS / 新闻聚合
- 公告抓取
- 财经新闻摘要
- Markdown / JSON 输出
- 可本地运行
- 可接入 Telegram 通知
- 适合作为"线索源"，不做交易建议
- 能服务 A 股盘前消息检查

### 排除

- 加密货币为主
- 自动交易
- broker connector
- long/short 信号
- AI 评级打分
- 需要高风险权限
- 主要服务美股且无法迁移到 A 股
- 只会输出买卖建议而不提供新闻来源

---

## 二、候选仓库列表

### P0：已评估，可直接使用

---

#### 1. ZhuLinsen/daily_stock_analysis

- **URL：** https://github.com/ZhuLinsen/daily_stock_analysis
- **Stars：** 39,498
- **语言：** Python
- **描述：** LLM 驱动的 A/H/美股智能分析：多数据源行情 + 实时新闻 + LLM 决策仪表盘 + 多渠道推送，零成本定时运行
- **审查状态：** ✅ 已完成（daily_stock_analysis_review_2026-06-01.md）
- **用途判断：** 最直接对标小工坊需求——A 股行情 + 实时新闻 + LLM 分析 + 多渠道推送。可作为盘前消息检查和每日持仓提醒的核心工具
- **A 股盘前消息：** ✅ 支持，含实时新闻模块
- **Telegram 接入：** ✅ 支持多渠道推送
- **风险点：** 依赖 LLM API；数据源依赖 akshare；需确认新闻模块的具体来源
- **优先级：** **P0**

---

### P1：值得只读审查

---

#### 2. Thysrael/Horizon

- **URL：** https://github.com/Thysrael/Horizon
- **Stars：** 5,205
- **语言：** Python
- **描述：** 📡 Your own AI-powered news radar. Generates daily briefings in English & Chinese. | 用 AI 构建你专属的新闻雷达
- **用途判断：** AI 新闻雷达，支持中英双语每日简报。可参考其新闻聚合 + AI 摘要 + 定时生成的架构。适合作为"盘前消息摘要"的参考实现
- **A 股盘前消息：** ⚠️ 需确认是否支持 A 股/财经新闻源自定义
- **Telegram 接入：** ⚠️ 需确认是否有推送能力
- **风险点：** 新闻源是否支持自定义（RSS/财经网站）；是否偏科技/通用新闻而非财经；LLM 依赖
- **优先级：** **P1**

---

#### 3. leiting-eric/DailyBrief

- **URL：** https://github.com/leiting-eric/DailyBrief
- **Stars：** 206
- **语言：** TypeScript
- **描述：** AI 每日新闻简报 · GitHub 热门 + X 热门文章 + 行情技术分析 · 23 个数据源聚合 + LLM 中文摘要 · 本地或 GitHub Actions 部署
- **用途判断：** 23 个数据源聚合 + LLM 中文摘要 + GitHub Actions 定时部署。含"行情技术分析"模块。可参考其数据源聚合 + 定时生成 + 部署架构
- **A 股盘前消息：** ⚠️ "行情技术分析"模块需确认是否支持 A 股；23 个数据源需确认是否含财经/公告源
- **Telegram 接入：** ⚠️ 需确认是否有推送能力
- **风险点：** TypeScript 栈，与小工坊 Python 生态不直接兼容；star 数较低（206）；主要功能是新闻聚合，股票分析可能只是附带
- **优先级：** **P1**

---

#### 4. iBigQiang/feedgrab

- **URL：** https://github.com/iBigQiang/feedgrab
- **Stars：** 469
- **语言：** Python
- **描述：** Universal content grabber — fetch, normalize, and digest content from 7+ platforms (WeChat, XHS, X/Twitter, YouTube, Bilibili, Telegram, RSS)
- **用途判断：** 通用内容抓取器，支持 7+ 平台（微信、小红书、X/Twitter、YouTube、Bilibili、Telegram、RSS）。可参考其 RSS 抓取 + 内容标准化 + 摘要生成架构。如果支持自定义 RSS 源，可接入财经 RSS
- **A 股盘前消息：** ⚠️ 不直接支持 A 股，但 RSS 模块可接入财经 RSS 源（如 Jin10 RSS、东方财富 RSS）
- **Telegram 接入：** ✅ 支持 Telegram 作为数据源之一
- **风险点：** 主要是内容聚合工具，非财经专用；需确认 RSS 自定义能力；摘要质量待验证
- **优先级：** **P1**

---

### P2：可参考但不直接适用

---

#### 5. 77AutumN/Intel_Briefing

- **URL：** https://github.com/77AutumN/Intel_Briefing
- **Stars：** 130
- **语言：** Python
- **描述：** 🕵️ AI 情报聚合系统 - 每日 Tech 热点、产品趋势、学术前沿追踪
- **用途判断：** AI 情报聚合，但偏科技/产品/学术方向，非财经。可参考其"每日简报"生成架构
- **A 股盘前消息：** ❌ 不支持，偏科技/学术
- **Telegram 接入：** ⚠️ 需确认
- **风险点：** 偏科技方向，非财经；star 数低（130）
- **优先级：** **P2**

---

#### 6. ourongxing/newsnow

- **URL：** https://github.com/ourongxing/newsnow
- **Stars：** 20,450
- **语言：** TypeScript
- **描述：** Elegant reading of real-time and hottest news
- **用途判断：** 实时热点新闻阅读器。可参考其新闻聚合和展示架构，但主要是阅读器而非自动化工具
- **A 股盘前消息：** ⚠️ 需确认新闻源是否支持财经/A 股
- **Telegram 接入：** ❌ 主要是 Web 阅读器
- **风险点：** TypeScript 栈；主要是阅读器，非自动化推送工具；20K star 但可能偏通用新闻
- **优先级：** **P2**

---

#### 7. koffuxu/ai-influence-digest

- **URL：** https://github.com/koffuxu/ai-influence-digest
- **Stars：** 316
- **语言：** Python
- **描述：** Turn X scrolling into an AI-powered weekly digest — no X API, no scraping, just your browser. Scans 65+ AI builders, filters actionable content, exports a poster
- **用途判断：** X/Twitter AI 影响者周报。可参考其"扫描 + 过滤 + 摘要 + 海报"架构，但数据源是 X/Twitter，非财经
- **A 股盘前消息：** ❌ 不支持，数据源是 X/Twitter
- **Telegram 接入：** ⚠️ 需确认
- **风险点：** 数据源是 X/Twitter，非财经；周报频率，非盘前实时
- **优先级：** **P2**

---

#### 8. unclecode/crawl4ai

- **URL：** https://github.com/unclecode/crawl4ai
- **Stars：** 67,338
- **语言：** Python
- **描述：** 🚀🤖 Crawl4AI: Open-source LLM Friendly Web Crawler & Scraper
- **用途判断：** 通用 LLM 友好爬虫。可用于抓取财经网站、公告页面、新闻页面。可作为"公告抓取"的底层工具
- **A 股盘前消息：** ⚠️ 不直接支持，但可用于抓取巨潮资讯、东方财富公告等页面
- **Telegram 接入：** ❌ 纯爬虫，无推送能力
- **风险点：** 通用爬虫，非财经专用；需要自行编写抓取规则；67K star 但需确认是否适合结构化数据抓取
- **优先级：** **P2**

---

#### 9. firecrawl/firecrawl

- **URL：** https://github.com/firecrawl/firecrawl
- **Stars：** 126,448
- **语言：** TypeScript
- **描述：** The API to search, scrape, and interact with the web at scale. 🔥
- **用途判断：** Web 抓取 API。可用于抓取财经网站和公告页面。可作为"公告抓取"的底层工具
- **A 股盘前消息：** ⚠️ 不直接支持，但可用于抓取 A 股公告页面
- **Telegram 接入：** ❌ 纯 API，无推送能力
- **风险点：** TypeScript 栈；通用抓取工具，非财经专用；126K star 但需要自行封装
- **优先级：** **P2**

---

#### 10. D4Vinci/Scrapling

- **URL：** https://github.com/D4Vinci/Scrapling
- **Stars：** 55,786
- **语言：** Python
- **描述：** 🕷️ An adaptive Web Scraping framework that handles everything from a single request to a full-scale crawl!
- **用途判断：** 自适应 Web 抓取框架。可用于抓取财经网站和公告页面
- **A 股盘前消息：** ⚠️ 不直接支持，但可用于抓取 A 股公告页面
- **Telegram 接入：** ❌ 纯抓取框架，无推送能力
- **风险点：** 通用抓取框架，非财经专用；需要自行编写抓取规则
- **优先级：** **P2**

---

### 排除

---

#### 11. 6551Team/opennews-mcp

- **排除原因：** 核心偏加密市场，A 股覆盖不足，AI 评级与 Trading Signal 风险较高
- **审查状态：** ✅ 已完成（opennews_mcp_review_2026-06-04.md）

#### 12. IvanWng97/TradingAgents-Telegram

- **排除原因：** 不支持 A 股，数据源是 yfinance + finviz
- **审查状态：** ✅ 已完成（tradingagents_telegram_review_2026-06-04.md）

#### 13. Open-Dev-Society/OpenStock

- **排除原因：** TypeScript 全栈平台，改造成本高，部署复杂

#### 14. Usagi-org/ai-goofish-monitor

- **排除原因：** 闲鱼监控工具，非财经新闻

#### 15. bwjoke/fomo5000.com

- **排除原因：** 仅美股市场地图，对 A 股无价值

---

## 三、推荐第一批只读审查

### 第 1 个：Thysrael/Horizon（P1）

理由：

- 5,205 stars，Python，AI 新闻雷达
- 支持中英双语每日简报
- "新闻雷达"定位最接近"盘前消息检查"
- 需确认：新闻源是否支持自定义 RSS/财经源、是否有 Telegram 推送

### 第 2 个：leiting-eric/DailyBrief（P1）

理由：

- 23 个数据源聚合 + LLM 中文摘要
- 含"行情技术分析"模块
- GitHub Actions 定时部署（可参考其自动化架构）
- 需确认：数据源是否含财经/A 股、是否有推送能力

### 第 3 个：iBigQiang/feedgrab（P1）

理由：

- 通用内容抓取器，支持 RSS
- Python，469 stars
- 如果 RSS 模块支持自定义源，可接入 Jin10/东方财富等财经 RSS
- 需确认：RSS 自定义能力、摘要生成质量

---

## 四、盘前消息自动化 v0.1 推荐路线

### 目标

每天早上 9:00 前，自动产出一份盘前消息摘要，包含：

- 外围市场动态（美股/港股收盘、汇率、原油）
- 宏观政策消息（央行、财政、贸易）
- A 股重大公告（业绩预告、重大合同、股权变动）
- 行业催化（新能源、储能、光伏）
- 个股相关消息（阳光电源等持仓标的）
- 市场情绪指标（融资余额、北向资金）

### 推荐路线

#### 第一步：用现有工具先跑起来（0 成本）

```
已有工具：
- daily_stock_analysis（P0，已在用）→ 行情 + 新闻 + LLM 分析
- akshare（已在用）→ A 股数据采集
- Perplexity（已在用）→ 交叉验证

先做：
1. 用 daily_stock_analysis 的新闻模块，跑一次盘前消息检查
2. 用 akshare 采集当日公告、业绩预告
3. 用 Perplexity 交叉验证重大消息
4. 输出 Markdown 盘前摘要
```

#### 第二步：补充 RSS 新闻源（低成本）

```
候选工具：
- Thysrael/Horizon → AI 新闻雷达，参考其新闻聚合架构
- iBigQiang/feedgrab → RSS 抓取，参考其 RSS 模块

做：
1. 审查 Horizon 和 feedgrab，确认是否支持自定义 RSS
2. 接入财经 RSS 源：
   - Jin10 金十数据 RSS
   - 东方财富公告 RSS
   - 新浪财经 RSS
   - 巨潮资讯公告 RSS
3. 用 LLM 对 RSS 内容做摘要
4. 输出 Markdown 盘前摘要
```

#### 第三步：接入 Telegram 推送（低成本）

```
候选方案：
- daily_stock_analysis 已有多渠道推送能力
- 自建简单 Telegram Bot 推送 Markdown 摘要

做：
1. 确认 daily_stock_analysis 的推送模块是否支持 Telegram
2. 如果不支持，自建简单 Telegram Bot
3. 每天早上自动推送盘前摘要到 Telegram
```

#### 第四步：补充公告监控（中等成本）

```
候选工具：
- unclecode/crawl4ai → 抓取巨潮资讯、东方财富公告页面
- D4Vinci/Scrapling → 自适应抓取框架

做：
1. 审查 crawl4ai 和 Scrapling，确认抓取 A 股公告的可行性
2. 编写公告抓取规则（巨潮资讯、上交所、深交所）
3. 用 LLM 对公告做摘要和分类
4. 重大公告实时推送 Telegram
```

#### 第五步：新闻去重与优先级（低成本）

```
做：
1. 对采集到的新闻做去重（标题相似度 + 来源去重）
2. 按优先级排序：
   - 持仓标的直接相关 → 最高
   - 行业催化 → 高
   - 宏观政策 → 中
   - 通用市场消息 → 低
3. 输出分层摘要
```

### 技术栈推荐

| 层级 | 工具 | 说明 |
|------|------|------|
| 数据采集 | akshare + daily_stock_analysis | A 股行情 + 新闻 |
| RSS 聚合 | Horizon 或 feedgrab（待审查） | 财经 RSS 源 |
| 公告抓取 | crawl4ai 或 Scrapling（待审查） | 巨潮/东方财富公告 |
| AI 摘要 | LLM（DeepSeek / Claude） | 新闻摘要 + 分类 |
| 定时调度 | cron / GitHub Actions | 每日定时运行 |
| 推送 | Telegram Bot | 盘前摘要推送 |
| 存储 | Markdown 文件 | 与小工坊现有格式一致 |

### 成本估算

| 步骤 | 成本 | 说明 |
|------|------|------|
| 第一步 | 0 | 用已有工具 |
| 第二步 | 0 | RSS 免费 |
| 第三步 | 0 | Telegram Bot 免费 |
| 第四步 | 0 | 爬虫免费 |
| 第五步 | 0 | 纯逻辑处理 |
| LLM API | ~$0.01—0.05/天 | DeepSeek 极低成本 |

---

## 五、总结

| 仓库 | 优先级 | 用途 | A 股支持 | Telegram |
|------|--------|------|---------|----------|
| daily_stock_analysis | P0 | 行情+新闻+LLM+推送 | ✅ | ✅ |
| Horizon | P1 | AI 新闻雷达 | ⚠️ 待确认 | ⚠️ 待确认 |
| DailyBrief | P1 | 23 源聚合+LLM 摘要 | ⚠️ 待确认 | ⚠️ 待确认 |
| feedgrab | P1 | RSS 抓取+摘要 | ⚠️ RSS 可扩展 | ✅ |
| Intel_Briefing | P2 | AI 情报聚合 | ❌ | ⚠️ |
| newsnow | P2 | 新闻阅读器 | ⚠️ | ❌ |
| crawl4ai | P2 | 通用爬虫 | ⚠️ 可抓取公告 | ❌ |
| Scrapling | P2 | 抓取框架 | ⚠️ 可抓取公告 | ❌ |
| opennews-mcp | 排除 | 加密为主 | ❌ | — |
| TradingAgents-Telegram | 排除 | 美股为主 | ❌ | — |

**推荐第一批审查：** Horizon → DailyBrief → feedgrab
