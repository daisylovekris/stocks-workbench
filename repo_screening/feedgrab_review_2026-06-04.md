# iBigQiang/feedgrab 只读可用性评估｜2026-06-04

> 评估范围：只读公开 README 与项目结构，不 clone、不安装、不运行。
> 评估目标：判断该工具对股票小工坊"盘前消息自动化"信息源采集层的可用性。
> 评估时间：2026-06-04

---

## 一、核心功能

feedgrab 是一个通用内容抓取器，核心管道：

```
任意 URL → 平台检测（17+ 平台）→ 抓取内容 → 统一输出（Markdown + YAML front matter）
```

四种使用模式：

| 模式 | 功能 | 输出 |
|------|------|------|
| Python CLI/库 | 基础内容抓取 + 统一数据结构 | Markdown + YAML |
| Claude Code 技能 | 视频转录 + AI 分析 + 内容抓取 | 结构化分析报告 |
| MCP 服务器 | 暴露读取能力为 MCP 工具 | JSON（tool response） |
| Python 库 | 开发者集成 | Python 对象 |

---

## 二、支持的平台（17+）

### 核心平台

| 平台 | 抓取方式 | 视频/音频转录 |
|------|---------|-------------|
| **YouTube** | InnerTube API（零依赖零配额） | yt-dlp 字幕 → Groq Whisper |
| **Bilibili** | API 元数据 | 三级字幕回退 → Whisper |
| **X/Twitter** | GraphQL → FxTwitter → Syndication → oEmbed → Jina → Playwright（6 级回退） | — |
| **微信公众号** | Jina → Playwright → 搜狗搜索 → MP 后端 API 批量 | — |
| **小红书** | API → Pinia 注入 → Jina → Playwright 深度抓取 | — |
| **Telegram** | Telethon | — |
| **RSS** | feedparser | — |
| **GitHub** | REST API | — |
| **知乎** | API v4 → Playwright → Jina | — |
| **微博** | 移动端 API + SSR | — |
| **抖音** | CDP → Playwright → SSR → Jina | — |
| **HackerNews** | Firebase API v0 | — |
| **Medium** | Jina → JSON-LD → Stealth Browser | — |
| **Reddit** | old.reddit.com .json | — |
| **飞书/Lark** | Open API → CDP → Playwright → Jina | — |
| **知识星球** | HTTP cookie → CDP → Playwright → Jina | — |
| **小宇宙** | SSR | Groq Whisper |
| **喜马拉雅** | Web Revision API | Groq Whisper |
| **任意网页** | JSON-LD → Jina 兜底 | — |

### 付费墙突破

支持 300+ 付费墙网站（NYT/WSJ/FT/Economist/Bloomberg/SCMP 等），7 级回退：

JSON-LD → Googlebot UA → AMP → archive.today → Google Cache

---

## 三、RSS / Atom 支持

**支持。** 通过 feedparser 库解析 RSS/Atom feed。

```
feedgrab <rss_feed_url>
```

输出保存到 `output/RSS/` 目录，格式为 Markdown + YAML front matter。

**注意：** feedgrab 是 RSS 消费者（读取 RSS），不是 RSS 生产者（不生成 RSS 输出）。

---

## 四、是否适合财经新闻 / A 股盘前消息检查

**部分适合，作为信息源采集层。**

| 维度 | 评估 |
|------|------|
| 财经新闻 | ⚠️ 不直接支持财经新闻源，但可通过 RSS/网页抓取接入 |
| A 股公告 | ⚠️ 可通过网页抓取（巨潮资讯/东方财富公告页面） |
| 微信财经公众号 | ✅ 微信公众号抓取是核心能力 |
| 财经 RSS | ✅ 支持 RSS feed 抓取 |
| 行业新闻 | ⚠️ 需要自行配置信息源 |
| 付费墙财经媒体 | ✅ Bloomberg/WSJ/FT/Economist 付费墙突破 |

---

## 五、能抓取或聚合什么

| 类型 | 可行性 | 说明 |
|------|--------|------|
| **公司公告** | 🟡 中 | 可通过网页抓取巨潮资讯/东方财富公告页面 |
| **财经新闻** | 🟡 中 | 可通过 RSS + 付费墙突破（Bloomberg/WSJ/FT） |
| **行业新闻** | 🟡 中 | 可通过微信财经公众号 + RSS |
| **社媒/网页信息源** | ✅ 高 | 17+ 平台抓取是核心能力 |

---

## 六、输出形式

| 形式 | 支持情况 |
|------|---------|
| **Markdown + YAML front matter** | ✅ 主要输出，Obsidian 兼容 |
| **CSV** | ✅ 搜索结果汇总表 |
| **JSON** | ✅ 批量索引文件、去重索引 |
| **媒体文件** | ✅ MP4/MP3/SRT/图片 |
| **Obsidian Vault** | ✅ 直接写入 Obsidian vault |
| **RSS 输出** | ❌ 不支持 |
| **数据库** | ❌ 不支持 |
| **消息推送** | ❌ 不支持 |
| **网页** | ❌ 不支持 |

---

## 七、是否需要 API Key

**大部分平台不需要。**

| 平台 | 是否需要 Key | 说明 |
|------|-------------|------|
| RSS | ❌ | feedparser 免费 |
| HackerNews | ❌ | Firebase API 免费 |
| GitHub（公开仓库） | ❌ | 无 Key 限 60 req/hr |
| Medium | ❌ | Jina Reader 免费 |
| Reddit | ❌ | old.reddit.com .json 免费 |
| 微信公众号（搜狗） | ❌ | 搜狗搜索免费 |
| 小红书（API） | ❌ | xhshow 免费 |
| 微博 | ❌ | 移动端 API 免费 |
| 任意网页（Jina） | ❌ | Jina Reader 免费 |
| X/Twitter（基础） | ❌ | FxTwitter/Syndication 免费 |
| X/Twitter（完整） | ⚠️ | X_AUTH_TOKEN + X_CT0 |
| YouTube（转录） | ⚠️ | GROQ_API_KEY（免费） |
| Telegram | ⚠️ | TG_API_ID + TG_API_HASH |
| 飞书 | ⚠️ | FEISHU_APP_ID + FEISHU_APP_SECRET |

---

## 八、是否容易改造成"盘前消息自动化 v0.1"的信息源采集层

**中等难度。**

优势：

- Python 栈，与小工坊兼容
- RSS 抓取开箱即用
- 微信公众号抓取可接入财经公众号
- 付费墙突破可获取 Bloomberg/WSJ/FT 财经新闻
- 统一 Markdown 输出格式
- 全局去重索引

限制：

- 无定时调度能力（需要外部 cron）
- 无推送能力（需要外部推送）
- 无 AI 摘要能力（需要外部 LLM）
- 无新闻评分/过滤能力
- 需要二次整理输出格式

改造方式：

```
feedgrab 抓取财经 RSS + 微信公众号 + 网页
  → 输出 Markdown 文件
  → 外部脚本读取 + LLM 摘要
  → 输出盘前消息摘要
  → 外部推送（Telegram Bot）
```

---

## 九、与 Horizon 对比

| 维度 | Horizon | feedgrab | 优胜 |
|------|---------|----------|------|
| **定位** | 新闻聚合 + AI 摘要 + 推送 | 内容抓取 + 统一输出 | 不同层级 |
| **语言** | Python | Python | 平手 |
| **RSS 支持** | ✅ | ✅ | 平手 |
| **新闻去重** | ✅ 跨平台去重 | ✅ 全局去重索引 | 平手 |
| **AI 摘要** | ✅ LLM 摘要 | ❌ 无 AI 摘要 | Horizon |
| **推送渠道** | ✅ 飞书/钉钉/Slack/Webhook | ❌ 无推送 | Horizon |
| **微信公众号** | ❌ | ✅ 核心能力 | feedgrab |
| **付费墙突破** | ❌ | ✅ 300+ 站点 | feedgrab |
| **社媒抓取** | ⚠️ 有限 | ✅ 17+ 平台 | feedgrab |
| **视频转录** | ❌ | ✅ YouTube/Bilibili/播客 | feedgrab |
| **A 股公告抓取** | ⚠️ 需 RSS | ⚠️ 需网页抓取 | 平手 |
| **定时运行** | ✅ GitHub Actions cron | ❌ 需外部 cron | Horizon |
| **MCP Server** | ✅ | ✅ | 平手 |
| **成熟度** | 较高（5,205 stars） | 较低（469 stars） | Horizon |

### 结论

**哪个更适合做主工具？**
→ **Horizon。** 有 AI 摘要、有推送、有定时运行、有去重评分。作为盘前消息自动化的主工具更完整。

**哪个更适合做信息源补充？**
→ **feedgrab。** 微信公众号抓取、付费墙突破、社媒抓取是 Horizon 不具备的能力。作为信息源采集层补充 Horizon 的数据源更合适。

**哪个改造成本更低？**
→ **Horizon。** 开箱即用，只需配置 RSS 源。feedgrab 需要外部 cron + 外部 LLM + 外部推送，改造成本更高。

**推荐组合：**
→ Horizon 做主工具（RSS 聚合 + AI 摘要 + 推送），feedgrab 做信息源补充（微信公众号 + 付费墙 + 社媒）。

---

## 十、对股票小工坊的用途评估

| 用途 | 可行性 | 说明 |
|------|--------|------|
| **盘前消息源补充** | ✅ 高 | RSS + 微信公众号 + 付费墙突破 |
| **财经 RSS 源管理** | ✅ 高 | feedparser 开箱即用 |
| **个股相关新闻采集** | 🟡 中 | 可通过微信财经公众号 + 网页抓取 |
| **行业催化线索采集** | 🟡 中 | 可通过微信公众号 + RSS |
| **后续 Telegram 消息源** | ⚠️ 低 | 无推送能力，需要外部脚本 |
| **付费墙财经媒体** | ✅ 高 | Bloomberg/WSJ/FT/Economist 突破 |
| **微信财经公众号** | ✅ 高 | 核心能力 |

---

## 十一、风险点

| 风险 | 等级 | 说明 |
|------|------|------|
| **抓取源失效** | 🟡 中 | 平台反爬策略变化可能导致抓取失败 |
| **反爬限制** | 🟡 中 | 微信/小红书/抖音等平台有反爬，需 cookie 轮换 |
| **A 股财经源不足** | 🟡 中 | 无内置 A 股公告源，需自行配置 |
| **维护成本高** | 🟡 中 | 17+ 平台的抓取逻辑需要持续维护 |
| **输出格式需二次整理** | 🟡 中 | Markdown 输出需要外部脚本做 AI 摘要和推送 |
| **无定时调度** | 🟡 中 | 需要外部 cron 或 systemd timer |
| **无推送能力** | 🟡 中 | 需要外部 Telegram Bot 推送 |
| **付费墙突破合法性** | 🟡 中 | 付费墙突破可能涉及法律风险 |
| **无交易功能** | 🟢 低 | 纯内容抓取工具 |

---

## 十二、结论

**评级：只读参考 + 可选择性试跑 RSS 和微信公众号抓取**

理由：

1. **微信公众号抓取是独特能力。** Horizon 不具备，但财经公众号（如"券商中国""东方财富"等）是 A 股盘前消息的重要来源。
2. **付费墙突破是独特能力。** 可获取 Bloomberg/WSJ/FT 的财经新闻，但需注意法律风险。
3. **RSS 抓取开箱即用。** 可作为 Horizon 的 RSS 数据源补充。
4. **Python 栈兼容。** 与小工坊 Python 生态直接兼容。
5. **但缺少 AI 摘要和推送。** 需要外部 LLM + 外部推送，改造成本高于 Horizon。
6. **作为信息源采集层补充 Horizon 更合适。** 不作为主工具，而是补充 Horizon 不具备的抓取能力。

建议态度：

- ✅ 作为 Horizon 的信息源补充层
- ✅ 用于微信财经公众号抓取
- ✅ 用于 RSS 源管理
- ⚠️ 付费墙突破需注意法律风险
- ❌ 不作为盘前消息自动化的主工具
- ❌ 不用于生成买卖建议

---

## 十三、后续试跑方案：只读信息源采集

**前提：** 只用于信息源采集，不涉及交易、买卖建议或券商权限。

### 第一步：RSS 抓取试跑

```bash
# 安装
pip install git+https://github.com/iBigQiang/feedgrab.git

# 抓取财经 RSS
feedgrab https://rsshub.app/jin10
feedgrab https://rsshub.app/eastmoney/report
feedgrab https://rsshub.app/sina/finance/roll

# 输出到 output/RSS/ 目录
```

### 第二步：微信公众号抓取试跑

```bash
# 配置搜狗搜索
export MPWEIXIN_SOGOU_ENABLED=true

# 抓取财经公众号
feedgrab mpweixin-so 券商中国
feedgrab mpweixin-so 东方财富
feedgrab mpweixin-so 新浪财经
```

### 第三步：与 Horizon 集成

```
feedgrab 抓取微信公众号 + 付费墙新闻
  → 输出 Markdown 到指定目录
  → Horizon 读取该目录作为数据源
  → Horizon 做 AI 摘要 + 去重 + 推送
```

### 禁止事项

- ❌ 不用于生成买卖建议
- ❌ 不接入券商
- ❌ 不配置交易权限
- ❌ 不将抓取内容直接当作投资建议
- ❌ 不突破付费墙用于商业用途

---

## 附录：项目关键数据

| 项目 | 数据 |
|------|------|
| 仓库 | https://github.com/iBigQiang/feedgrab |
| License | MIT |
| 语言 | Python |
| Stars | 469 |
| 支持平台 | 17+（含 300+ 付费墙站点） |
| RSS 支持 | ✅（feedparser） |
| 输出格式 | Markdown + YAML / CSV / JSON / 媒体文件 |
| 推送能力 | ❌ 无 |
| AI 摘要 | ❌ 无（需外部 LLM） |
| 定时运行 | ❌ 需外部 cron |
| MCP Server | ✅ |
| 付费墙突破 | ✅（NYT/WSJ/FT/Economist/Bloomberg 等） |
| 微信公众号 | ✅ 核心能力 |
| A 股支持 | ⚠️ 需自行配置信息源 |
| 交易功能 | ❌ 无 |
