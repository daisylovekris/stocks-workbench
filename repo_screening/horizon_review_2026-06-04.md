# Thysrael/Horizon 只读可用性评估｜2026-06-04

> 评估范围：只读公开 README 与项目结构，不 clone、不安装、不运行。
> 评估目标：判断该工具对股票小工坊"盘前消息自动化"的可用性。
> 评估时间：2026-06-04

---

## 一、核心功能

Horizon 是一个 AI 驱动的个人新闻雷达，核心管道：

```
Fetch（抓取） → Deduplicate（去重） → AI Score & Filter（AI 评分过滤） → Enrich（富化） → Summary（摘要） → Deliver（推送）
```

关键特性：

- 7 大数据源：Hacker News、RSS/Atom、Reddit、Telegram、Twitter/X、GitHub、OpenBB（金融）
- AI 评分（0—10 分）自动过滤低质量内容
- 跨平台去重（合并同一事件的不同来源报道）
- 富化（通过 Web 搜索补充背景信息）
- 社区评论收集（HN/Reddit/Twitter 评论）
- 中英双语每日简报生成
- GitHub Actions 定时自动部署到 GitHub Pages
- MCP Server 集成（可暴露给 AI 助手调用）

---

## 二、新闻源是否支持自定义

**完全支持。** 所有新闻源通过单一 JSON 配置文件（`data/config.json`）管理。

### 支持的新闻源类型

| 来源 | 说明 | 评论支持 |
|------|------|---------|
| **Hacker News** | 按评分获取热门故事 | ✅（Top N 评论） |
| **RSS / Atom** | 任意 RSS/Atom feed URL | ❌ |
| **Reddit** | 子版块 + 用户帖子 | ✅（Top N 评论） |
| **Telegram** | 公开频道消息 | ❌ |
| **Twitter / X** | 指定用户推文 | ✅（Top N 回复） |
| **GitHub** | 用户事件 & 仓库 Release | ❌ |
| **OpenBB** | 按 watchlist/provider 获取金融公司新闻 | ❌ |

配置示例（RSS）：

```json
{
  "rss": [
    {"url": "https://feeds.feedburner.com/example"}
  ]
}
```

还有社区源发现平台（horizon1123.top）和设置向导（`uv run horizon-wizard`）。

---

## 三、是否支持 RSS

**完全支持。** RSS/Atom 是核心数据源之一，用户只需在配置中提供 feed URL。

这意味着可以接入：

- Jin10 金十数据 RSS
- 东方财富公告 RSS
- 新浪财经 RSS
- 巨潮资讯公告 RSS
- 任何其他财经 RSS 源

---

## 四、是否适合财经新闻 / A 股盘前消息检查

**适合，但需要自定义配置。**

| 维度 | 评估 |
|------|------|
| 默认新闻源 | ⚠️ 偏科技/AI（HN、Reddit、GitHub），不含财经 |
| RSS 可扩展性 | ✅ 可接入任意财经 RSS 源 |
| OpenBB 金融新闻 | ✅ 支持按 watchlist 获取金融公司新闻 |
| A 股公告 | ⚠️ 不直接支持，但可通过 RSS 接入巨潮/东方财富公告 |
| A 股行业新闻 | ⚠️ 需要自行配置财经 RSS 源 |
| 中文支持 | ✅ 支持中文摘要生成 |

**关键优势：** OpenBB 数据源直接支持金融公司新闻，RSS 可扩展到任意财经源。

**关键限制：** 默认配置不含 A 股/财经源，需要自行配置。

---

## 五、是否支持中文摘要

**支持。** 中英双语每日简报是核心特性。

- 可同时生成英文和中文简报
- 中文文档（README_zh.md）说明对中文用户友好
- LLM 配置支持中文模型（DeepSeek、Doubao、MiniMax 等）

---

## 六、是否支持定时生成每日简报

**支持。**

- 内置 GitHub Actions 工作流（`.github/workflows/daily-summary.yml`）
- 可配置为 cron 定时运行
- 自动生成并部署到 GitHub Pages
- 输出保存到 `data/summaries/`
- 支持本地 cron 或 GitHub Actions 两种定时方式

---

## 七、是否支持推送

**支持多种推送渠道：**

| 渠道 | 支持情况 | 说明 |
|------|---------|------|
| **Email** | ✅ | 自托管 SMTP/IMAP newsletter，支持订阅/退订 |
| **飞书（Feishu/Lark）** | ✅ | Webhook 模板推送 |
| **钉钉（DingTalk）** | ✅ | Webhook 推送 |
| **Slack** | ✅ | Webhook 推送 |
| **Discord** | ✅ | Webhook 推送 |
| **自定义 Webhook** | ✅ | 任意 Webhook URL |
| **MCP Server** | ✅ | 暴露给 AI 助手调用 |
| **Telegram** | ❌ | 未直接支持，但可通过自定义 Webhook 间接实现 |

**Telegram 缺失是关键限制。** 但自定义 Webhook 可以桥接到 Telegram Bot API。

---

## 八、输出形式

| 形式 | 支持情况 |
|------|---------|
| **Markdown** | ✅ 主要输出格式 |
| **GitHub Pages 网页** | ✅ 自动部署 |
| **Email newsletter** | ✅ |
| **Webhook 推送** | ✅ 飞书/钉钉/Slack/Discord/自定义 |
| **JSON** | ⚠️ 未明确，但 Webhook 推送可能包含结构化数据 |
| **MCP tool response** | ✅ |

---

## 九、是否需要 LLM API Key

**是的，必须配置。**

支持的 LLM 提供商：

| 提供商 | 说明 |
|--------|------|
| Claude（Anthropic） | — |
| GPT（OpenAI） | 任何 OpenAI 兼容 API |
| Gemini（Google） | 使用 GOOGLE_API_KEY |
| DeepSeek | — |
| Doubao（豆包） | — |
| MiniMax | — |
| OpenClaw | — |
| Ollama | 本地免费 |
| 任意 OpenAI 兼容 API | 自定义 base_url |

配置方式：在 `data/config.json` 中设置 provider、model、api_key_env。

---

## 十、对股票小工坊的用途评估

| 用途 | 可行性 | 说明 |
|------|--------|------|
| **盘前消息摘要** | ✅ 高 | RSS + OpenBB + 中文摘要 + 定时生成，最匹配 |
| **外围消息汇总** | ✅ 高 | 可接入全球财经 RSS、HN、Reddit 等 |
| **行业催化整理** | ✅ 高 | 可配置行业相关 RSS 源 |
| **新闻去重与分层** | ✅ 高 | 跨平台去重 + AI 评分过滤是核心能力 |
| **每日简报结构参考** | ✅ 高 | Fetch→Dedup→Score→Enrich→Summary→Deliver 管道可直接参考 |
| **A 股公告监控** | 🟡 中 | 需通过 RSS 接入巨潮/东方财富公告 |
| **Telegram 推送** | ⚠️ 需改造 | 不直接支持 Telegram，需通过自定义 Webhook 桥接 |

---

## 十一、风险点

| 风险 | 等级 | 说明 |
|------|------|------|
| **新闻源偏通用** | 🟡 中 | 默认配置不含财经/A 股源，需要自行配置 RSS |
| **LLM 摘要可能漏掉重要信息** | 🟡 中 | AI 评分过滤可能误杀重要但低分的财经消息 |
| **推送配置可能涉及 token** | 🟡 中 | 飞书/钉钉/Slack Webhook 需要配置 token |
| **Telegram 不直接支持** | 🟡 中 | 需要通过自定义 Webhook 桥接到 Telegram Bot API |
| **需要较多改造才能服务 A 股** | 🟡 中 | 需要配置财经 RSS 源、OpenBB watchlist、中文 LLM |
| **OpenBB 可能需要额外安装** | 🟡 中 | OpenBB 是可选依赖（`uv sync --extra openbb`） |
| **LLM 幻觉** | 🟡 中 | 摘要和评分由 LLM 生成，存在幻觉风险 |
| **无交易功能** | 🟢 低 | 纯新闻聚合工具，无交易能力 |

---

## 十二、结论

**评级：立刻可试**

理由：

1. **RSS 完全支持。** 可接入任意财经 RSS 源（Jin10、东方财富、新浪财经、巨潮资讯），直接服务 A 股盘前消息检查。
2. **OpenBB 金融新闻。** 直接支持按 watchlist 获取金融公司新闻，天然适合股票场景。
3. **中英双语摘要。** 中文摘要是核心特性，不需要额外改造。
4. **定时生成 + 自动部署。** GitHub Actions cron 内置，可直接用于每日盘前简报。
5. **跨平台去重 + AI 评分。** 新闻去重和质量过滤是核心能力，正是小工坊需要的。
6. **多渠道推送。** 支持飞书/钉钉/Slack/Discord/Email，Telegram 可通过 Webhook 桥接。
7. **MCP Server。** 可集成到 Claude Code，作为 AI 助手的新闻工具。

建议态度：

- ✅ 立刻可试，作为盘前消息自动化的核心工具
- ✅ 配置财经 RSS 源（Jin10、东方财富、新浪财经）
- ✅ 配置 OpenBB watchlist（阳光电源等持仓标的）
- ✅ 用 DeepSeek 作为 LLM（低成本）
- ✅ 通过自定义 Webhook 桥接到 Telegram
- ⚠️ 默认配置偏科技，需要自行定制财经配置
- ❌ 不涉及交易、买卖建议或券商权限

---

## 十三、后续试跑方案：新闻简报只读生成

**前提：** 只用于新闻简报生成，不涉及交易、买卖建议或券商权限。

### 第一步：最小化本地试跑

```bash
# 1. Clone
git clone https://github.com/Thysrael/Horizon.git
cd Horizon

# 2. 安装
uv sync

# 3. 配置
cp .env.example .env
cp data/config.example.json data/config.json
# 编辑 .env，配置 LLM API Key（如 DeepSeek）
# 编辑 data/config.json，添加财经 RSS 源

# 4. 运行设置向导
uv run horizon-wizard

# 5. 运行
uv run horizon --hours 24
```

### 第二步：配置财经 RSS 源

在 `data/config.json` 中添加：

```json
{
  "rss": [
    {"url": "https://rsshub.app/jin10"},
    {"url": "https://rsshub.app/eastmoney/report"},
    {"url": "https://rsshub.app/sina/finance/roll"},
    {"url": "https://rsshub.app/cninfo/announcement"}
  ],
  "openbb": {
    "watchlist": ["300274.SZ", "601012.SH"],
    "provider": "benzinga"
  }
}
```

**注意：** 以上 RSS URL 需要验证是否可用（RSSHub 路径可能需要调整）。

### 第三步：配置 LLM

```json
{
  "ai": {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "api_key_env": "DEEPSEEK_API_KEY",
    "base_url": "https://api.deepseek.com"
  }
}
```

### 第四步：配置推送（可选）

通过自定义 Webhook 桥接到 Telegram：

```json
{
  "delivery": {
    "webhook": {
      "url": "https://api.telegram.org/bot<TOKEN>/sendMessage",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  }
}
```

**注意：** Telegram Bot API 需要 bot token，但这是推送配置，不是交易权限。

### 第五步：定时运行

```bash
# 本地 cron（每天早上 8:30 运行）
30 8 * * * cd /path/to/Horizon && uv run horizon --hours 24

# 或使用 GitHub Actions（已内置）
```

### 禁止事项

- ❌ 不用于生成买卖建议
- ❌ 不接入券商
- ❌ 不配置交易权限
- ❌ 不将 AI 评分直接用于操作决策
- ❌ 不将简报内容直接当作投资建议

---

## 附录：项目关键数据

| 项目 | 数据 |
|------|------|
| 仓库 | https://github.com/Thysrael/Horizon |
| License | MIT |
| 语言 | Python（99.6%） |
| Stars | 5,205 |
| Forks | 763 |
| 数据源 | 7 类（HN/RSS/Reddit/Telegram/Twitter/GitHub/OpenBB） |
| AI 功能 | 评分（0—10）、去重、富化、中英摘要 |
| 推送渠道 | Email/飞书/钉钉/Slack/Discord/自定义 Webhook/MCP |
| 定时运行 | GitHub Actions cron 内置 |
| LLM 提供商 | Claude/GPT/Gemini/DeepSeek/Doubao/MiniMax/Ollama 等 |
| Telegram 支持 | ❌ 不直接支持，可通过 Webhook 桥接 |
| A 股支持 | ⚠️ 需通过 RSS 自定义配置 |
| 交易功能 | ❌ 无 |
