# leiting-eric/DailyBrief 只读可用性评估｜2026-06-04

> 评估范围：只读公开 README 与项目结构，不 clone、不安装、不运行。
> 评估目标：判断该工具对股票小工坊"盘前消息自动化"的可用性。
> 评估时间：2026-06-04

---

## 一、核心功能

DailyBrief 是一个 AI 驱动的每日新闻聚合工具，核心管道：

```
23 数据源抓取 → LLM 中文摘要 → 21 个行情 ticker 技术分析 → 单文件 HTML 报告 → GitHub Pages 部署
```

关键特性：

- 23 个数据源（科技/金融/政治/社区）
- 21 个行情 ticker（美股/加密/港股/商品/外汇/宏观）+ SMA/RSI/MACD 技术指标 + AI 交易评论
- 5 个 LLM 后端可切换（Claude CLI/Anthropic/OpenAI/DeepSeek/MiniMax）
- 中英双语（`REPORT_LOCALE=zh` 或 `en`）
- 三种部署方式：GitHub Actions + Pages、本地定时、AI Agent 安装
- 数据源零成本（全部免费公开 RSS/JSON 端点）
- 单文件 HTML 输出（CSS/JS 内联，无外部依赖）
- Markdown 输出可选（`OUTPUT_MARKDOWN=true`）

---

## 二、是否支持 RSS / 新闻源自定义

**支持。** 新闻源通过 `sources.config.json` 配置，每个源支持 `type` 字段：`rss`、`api` 或 `scrape`。

添加新 RSS 源的步骤：

1. 在 `sources.config.json` 中添加条目
2. 运行 `npm run sources:check` 验证格式
3. 运行 `npm run dry-run` 确认抓取成功
4. 下次 `npm run daily` 自动生效

配置字段：`id`、`name`、`type`、`url`、`category`、`subcategory`、`enabled`、`useCurl`、`lang`、`locales`、`notes`

---

## 三、23 个数据源详情

### 科技类

| # | 来源 | 说明 |
|---|------|------|
| 1 | GitHub Trending | 每日热门仓库 |
| 2 | AI 媒体合并源 | OpenAI Blog、DeepMind Blog、Hugging Face Blog、TLDR AI、Smol AI、Latent Space、MIT Tech Review |
| 3 | X/Twitter AI 大V | attentionvc-ai 精选 AI 思想领袖 |

### 金融类（21 个行情 ticker）

| # | Ticker | 说明 |
|---|--------|------|
| 4—11 | SPY/QQQ/AAPL/MSFT/NVDA/GOOGL/TSLA/META | 美股 |
| 12—14 | BTC/ETH/SOL | 加密货币 |
| 15—17 | BABA/PDD/JD | 中概股 |
| 18 | 0700.HK | 腾讯 |
| 19—20 | GC=F/CL=F | 黄金/WTI 原油 |
| 21 | USDCNY=X | 美元/人民币 |
| 22—24 | ^VIX/^TNX/DXY | VIX/10Y 国债/美元指数 |

附加：Crypto Fear & Greed Index、CoinGecko 宏观概览

### 国际新闻类（7 个）

BBC、Guardian、NYT、NPR、DW 中文、Al Jazeera、The Diplomat

### 财经新闻类（5 个）

Bloomberg、WSJ、FT、BBC Business、Economist

### 社区类

- 中文模式：V2EX 热门、LinuxDo 趋势
- 英文模式：Hacker News、Reddit r/stocks

---

## 四、是否适合财经新闻 / A 股盘前消息检查

**部分适合，但有明显限制。**

| 维度 | 评估 |
|------|------|
| 财经新闻源 | ✅ 5 个主流财经媒体（Bloomberg/WSJ/FT/BBC Business/Economist） |
| A 股个股 | ❌ 不支持，无 A 股个股 ticker |
| A 股公告 | ❌ 不支持 |
| 中概股 | ⚠️ 仅 BABA/PDD/JD，覆盖面极窄 |
| 港股 | ⚠️ 仅腾讯 0700.HK |
| 宏观指标 | ✅ VIX/10Y 国债/美元指数/美元人民币/黄金/原油 |
| 行业新闻 | ❌ 无新能源/储能/光伏行业新闻源 |
| RSS 可扩展 | ✅ 可添加财经 RSS 源 |

**关键限制：** 21 个 ticker 中没有 A 股个股，5 个财经新闻源都是国际媒体，不覆盖 A 股公告和行业新闻。

**关键优势：** 宏观指标覆盖好（VIX/汇率/国债/商品），RSS 可扩展。

---

## 五、是否支持中文摘要

**支持。** 默认 `zh` 模式：

- 20 个全球英文源自动生成中文摘要
- 中文 UI 文本
- 立场标签：偏上行 / 偏下行 / 中性
- `zh-CN` 日期格式

---

## 六、是否支持 GitHub Actions 定时运行

**支持。** 这是推荐部署方式（Path A）。

- GitHub Actions cron 每小时运行一次
- gate 作业检查当前时间是否匹配 `REPORT_HOUR`/`REPORT_DAYS`
- 支持 DST 自动处理
- 常用配置：
  - 每天 08:00：`REPORT_HOUR=8`
  - 每天两次：`REPORT_HOUR=8,18`
  - 工作日 09:00：`REPORT_HOUR=9, REPORT_DAYS=1-5`
- GitHub Actions + Pages 在公开仓库免费
- LLM 成本：DeepSeek < $1/月，Anthropic Sonnet < $2/月

---

## 七、是否支持推送

**不支持。**

- 没有 Telegram 推送
- 没有邮件推送
- 没有 Webhook 推送
- 输出是静态 HTML，用户需要访问 URL 查看
- 自托管部署用 `scp` 推送到远程服务器，但不是用户通知

**这是与 Horizon 相比的关键劣势。**

---

## 八、输出形式

| 形式 | 支持情况 |
|------|---------|
| **HTML（单文件）** | ✅ 主要输出，CSS/JS 内联，无外部依赖 |
| **JSON（缓存）** | ✅ 文章数据缓存 |
| **Markdown** | ⚠️ 可选（`OUTPUT_MARKDOWN=true`） |
| **GitHub Pages 网站** | ✅ 索引页 + 归档 |
| **消息推送** | ❌ 不支持 |

---

## 九、是否需要 LLM API Key

**是的，必须配置。**

| 后端 | Key 变量 | 默认模型 |
|------|---------|---------|
| claude-cli | 无（用 Claude Code OAuth） | sonnet |
| anthropic | ANTHROPIC_API_KEY | claude-sonnet-4-6 |
| openai | OPENAI_API_KEY | gpt-4o-mini |
| deepseek | DEEPSEEK_API_KEY | deepseek-v4-flash |
| minimax | MINIMAX_API_KEY | MiniMax-M2.7 |

还支持 OpenAI 兼容代理（Moonshot/SiliconFlow/OpenRouter/Ollama/LM Studio）。

---

## 十、对股票小工坊的用途评估

| 用途 | 可行性 | 说明 |
|------|--------|------|
| **盘前消息摘要** | 🟡 中 | 有 5 个财经新闻源，但不覆盖 A 股公告 |
| **每日持仓相关新闻** | 🔴 低 | 无 A 股个股 ticker，无法跟踪阳光电源等 |
| **行业催化整理** | 🔴 低 | 无新能源/储能/光伏行业新闻源 |
| **外围消息汇总** | ✅ 高 | 宏观指标（VIX/汇率/国债/商品）+ 国际财经媒体 |
| **定时简报结构参考** | ✅ 高 | GitHub Actions cron + gate 作业 + HTML 报告结构可参考 |
| **技术指标参考** | 🟡 中 | SMA/RSI/MACD + AI 交易评论，但偏美股 ticker |

---

## 十一、与 Horizon 对比

| 维度 | Horizon | DailyBrief | 优胜 |
|------|---------|------------|------|
| **语言** | Python | TypeScript | Horizon（小工坊用 Python） |
| **数据源** | 7 类（HN/RSS/Reddit/Telegram/Twitter/GitHub/OpenBB） | 23 个固定源 | Horizon（RSS 更灵活） |
| **RSS 支持** | ✅ 完全支持 | ✅ 支持 | 平手 |
| **A 股支持** | ⚠️ 需自定义 RSS | ❌ 无 A 股 ticker | Horizon |
| **中文摘要** | ✅ | ✅ | 平手 |
| **定时运行** | ✅ GitHub Actions | ✅ GitHub Actions | 平手 |
| **推送渠道** | ✅ Email/飞书/钉钉/Slack/Discord/Webhook | ❌ 无推送 | Horizon |
| **Telegram** | ⚠️ 可通过 Webhook 桥接 | ❌ 不支持 | Horizon |
| **输出格式** | Markdown + GitHub Pages | HTML 单文件 + GitHub Pages | 平手 |
| **行情 ticker** | ❌ 无 | ✅ 21 个 ticker + 技术指标 | DailyBrief |
| **去重能力** | ✅ 跨平台去重 | ❌ 无去重 | Horizon |
| **AI 评分** | ✅ 0—10 分 | ❌ 无评分 | Horizon |
| **OpenBB 金融** | ✅ | ❌ | Horizon |
| **Stars** | 5,205 | 206 | Horizon |
| **成熟度** | 较高 | 较低 | Horizon |

### 结论对比

**哪个更适合做盘前消息自动化 v0.1？**
→ **Horizon。** RSS 更灵活、有推送渠道、有去重能力、Python 栈。

**哪个更轻？**
→ **DailyBrief。** 一键部署、固定源、单文件输出。但缺少推送是硬伤。

**哪个更容易接入股票小工坊？**
→ **Horizon。** Python 栈、RSS 可扩展、MCP Server 集成。

**哪个更适合后续接 Telegram？**
→ **Horizon。** 有自定义 Webhook，可桥接 Telegram Bot API。DailyBrief 完全不支持推送。

---

## 十二、风险点

| 风险 | 等级 | 说明 |
|------|------|------|
| **新闻源偏通用** | 🔴 高 | 23 个源中无 A 股公告、无行业新闻 |
| **A 股覆盖不足** | 🔴 高 | 21 个 ticker 中无 A 股个股 |
| **无推送能力** | 🔴 高 | 不支持 Telegram/邮件/Webhook，需要用户主动访问 |
| **TypeScript 栈** | 🟡 中 | 与小工坊 Python 生态不直接兼容 |
| **LLM 摘要可能漏信息** | 🟡 中 | AI 生成的摘要可能遗漏重要财经消息 |
| **GitHub Actions 成本** | 🟢 低 | 公开仓库免费，LLM 成本 < $2/月 |
| **无交易功能** | 🟢 低 | 纯新闻聚合工具 |

---

## 十三、结论

**评级：只读参考**

理由：

1. **A 股覆盖不足。** 21 个 ticker 无 A 股个股，23 个源无 A 股公告/行业新闻。
2. **无推送能力。** 不支持 Telegram/邮件/Webhook，用户需要主动访问 URL，不适合"盘前自动推送"场景。
3. **TypeScript 栈。** 与小工坊 Python 生态不直接兼容。
4. **与 Horizon 相比劣势明显。** Horizon 在 RSS 灵活性、推送渠道、去重能力、A 股可扩展性、Python 栈等方面全面优于 DailyBrief。

建议态度：

- ✅ 参考其 GitHub Actions cron + gate 作业的定时架构
- ✅ 参考其 21 个 ticker + SMA/RSI/MACD 的行情技术分析结构
- ✅ 参考其 HTML 单文件报告的输出格式
- ❌ 不作为盘前消息自动化的核心工具
- ❌ 不用于 A 股盘前消息检查
- ⚠️ 如果 Horizon 试跑成功，不需要再试 DailyBrief

---

## 十四、不建议试跑

由于 A 股覆盖不足、无推送能力、TypeScript 栈与小工坊不兼容，且 Horizon 在各方面更优，不建议后续试跑 DailyBrief。

如果需要参考其架构，只需阅读源码即可，不需要实际运行。

---

## 附录：项目关键数据

| 项目 | 数据 |
|------|------|
| 仓库 | https://github.com/leiting-eric/DailyBrief |
| License | MIT |
| 语言 | TypeScript（84.9%）+ JavaScript（15.1%） |
| Stars | 206 |
| Forks | 105 |
| 数据源 | 23 个（科技/金融/政治/社区） |
| 行情 ticker | 21 个（美股/加密/中概/港股/商品/外汇/宏观） |
| 技术指标 | SMA / RSI / MACD + AI 交易评论 |
| LLM 后端 | 5 个（Claude CLI/Anthropic/OpenAI/DeepSeek/MiniMax） |
| 推送渠道 | ❌ 无 |
| 输出格式 | HTML 单文件 + JSON 缓存 + 可选 Markdown |
| 定时运行 | ✅ GitHub Actions cron |
| A 股支持 | ❌ 无 A 股个股 ticker |
| 交易功能 | ❌ 无 |
