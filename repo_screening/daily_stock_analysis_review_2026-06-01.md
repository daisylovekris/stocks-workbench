# daily_stock_analysis 项目可用性评估报告

- **仓库：** github.com/ZhuLinsen/daily_stock_analysis
- **语言：** Python 78.1% / TypeScript 18.9%
- **热度：** 39,498 stars / 38,200 forks / v3.19.0（2026-05-29）/ MIT License
- **评估日期：** 2026-06-01
- **评估方式：** 只读审查公开 README 和项目结构，未 clone、未安装、未运行

---

## 1. 核心功能

LLM 驱动的多市场智能股票分析系统。完整流程：

- **数据采集：** 多源行情（K 线、资金流、筹码、基本面）+ 实时新闻 + 公告
- **AI 分析：** LLM 生成"决策仪表盘"——评分、趋势、买/卖点、风险提示、催化剂、操作清单
- **Agent 策略问答：** 15+ 内置策略（均线、缠论、波浪、趋势、事件驱动、成长质量等），支持多轮对话
- **多渠道推送：** Telegram、企业微信、飞书、钉钉、邮件、Discord、Slack 等 11 种渠道
- **Web 工作台：** 配置管理、任务监控、历史报告浏览、回测、组合管理、深浅主题
- **自动化调度：** GitHub Actions / Docker / 本地 cron，工作日 18:00 自动执行

**不包含任何交易下单功能。** main.py 确认为纯分析 + 通知系统，无买入/卖出执行逻辑。

---

## 2. 是否支持 A 股？能否分析阳光电源 300274？

**是，原生支持 A 股。** 配置说明明确列出深市 300xxx 代码格式。`STOCK_LIST` 配置示例：

```
STOCK_LIST=300274
```

即可分析阳光电源。同时支持港股（hk00700）、美股（AAPL）和 ETF。

---

## 3. 数据源

### 行情数据源（7 个，按优先级排列）

- **efinance**（东方财富，优先级 0 = 最高）
- **AkShare**（优先级 1）
- **Tushare**（优先级 2，需 Token）
- **Pytdx**（通达信，优先级 2）
- **Baostock**（优先级 3）
- **YFinance**（优先级 4）
- **Longbridge**（需 OAuth）
- **TickFlow**（大盘复盘指数增强）

### 新闻搜索源（6 个）

- Anspire（中文优化，推荐）、SerpAPI、Tavily、Bocha、Brave、MiniMax、SearXNG

### A 股最小依赖

只需 efinance + AkShare（均免费、无需 Token），已内置在 requirements.txt 中。数据源带优先级降级机制，单个接口失效不影响整体。

---

## 4. 是否必须配置 LLM API Key？

**是，至少需要一个 LLM Key。** 支持 15+ 厂商：

- **推荐（低门槛）：** Anspire（含免费额度，一个 Key 同时提供模型 + 搜索）、AIHubMix
- **主流：** Gemini、OpenAI、DeepSeek、Anthropic Claude、通义千问
- **本地免费：** Ollama（无需 Key，但需要本地 GPU）

如果只为测试，Ollama 本地模型可以零成本运行。

---

## 5. 输出形式

- **决策仪表盘：** Markdown 格式，含评分、趋势、风险提示、催化剂、操作清单
- **大盘复盘：** 指数涨跌、涨跌家数、涨停跌停、板块领涨领跌
- **Web 工作台：** 浏览器访问，完整 Markdown 渲染、历史报告、回测、组合管理
- **推送消息：** 根据渠道自动转为文本 / 图片（Markdown-to-Image 支持）
- **数据库：** SQLite 本地存储（`./data/stock_analysis.db`）

---

## 6. 推送能力

**支持 11 种推送渠道：**

- Telegram（Bot Token + Chat ID）
- 企业微信（Webhook）
- 飞书（Webhook / Stream Bot / 云文档）
- 钉钉（AppKey / Stream）
- 邮件（SMTP）
- Discord（Webhook / Bot）
- Slack（Bot / Webhook）
- Server酱3、Pushover、ntfy、Gotify、PushPlus、AstrBot
- 自定义 Webhook（Bearer Token + JSON 模板）

还支持：通知去重、冷却限频、静默时段、最低级别过滤、分组推送。

**支持本地只生成报告、不推送：** 不配置任何推送渠道变量时，报告只输出到终端/日志/WebUI，不会发送到外部平台。`--dry-run` 模式可干跑验证配置。

---

## 7. 本地运行依赖复杂度

**requirements.txt 共 39 个包，复杂度中等偏高。**

核心依赖：
- 数据层：pandas、numpy、akshare、tushare、efinance、baostock、pytdx、yfinance
- AI 层：litellm、openai、tiktoken
- 推送层：lark-oapi、discord.py、requests
- Web 层：fastapi、uvicorn、jinja2
- 工具层：schedule、exchange-calendars、sqlalchemy

Python 版本：3.10-3.12（基于 black 配置推断）

与 stock-analysis 项目（仅 3 个包）相比，依赖显著更重，但仍在常规 Python 项目范围内。无 C 扩展编译需求。

---

## 8. 对股票小工坊的用途

- **每日持仓提醒：** **完美匹配。** 配置 `STOCK_LIST=300274,000762,...` + Telegram 推送，工作日自动执行
- **个股新闻异动：** **支持。** 6 个新闻源 + 事件告警监控（`AGENT_EVENT_MONITOR_ENABLED`），支持价格穿越、涨跌幅、成交量异动告警
- **技术面摘要：** **支持。** 内置实时技术指标计算（`ENABLE_REALTIME_TECHNICAL_INDICATORS`），15+ 策略覆盖均线、缠论、波浪等
- **风险位提醒：** **支持。** 内置乖离率阈值（`BIAS_THRESHOLD=5%`）、止损告警（`PORTFOLIO_RISK_STOP_LOSS_ALERT_PCT`）、回撤告警、集中度风险告警
- **多股观察：** **支持。** `STOCK_LIST` 支持任意数量股票，分组推送（`STOCK_GROUP_N` + `EMAIL_GROUP_N`）

### 与现有小工坊的整合价值

- **直接替代手工分析流程：** 自动采集 + AI 分析 + 定时推送，完美匹配"每日持仓提醒"
- **补充小工坊缺失能力：** 新闻聚合、事件告警、技术指标、回测、Web 工作台
- **与 stock-analysis 互补：** stock-analysis 做深度单股报告，daily_stock_analysis 做每日多股巡检

---

## 9. 风险点

- **自动交易风险：** **不存在。** main.py 确认无任何交易执行代码，纯分析 + 通知系统
- **API Key 泄露风险：** **存在。** 170+ 配置变量，至少需要 1 个 LLM Key + 1 个推送渠道 Key。建议使用 GitHub Secrets 或 `.env` 文件，不提交到 git
- **数据源失效风险：** **低。** 7 个数据源带优先级降级机制，单个接口失效不影响整体
- **LLM 幻觉风险：** **存在。** AI 分析结果可能包含不准确的判断，需人工复核。项目自带回测模块可部分缓解
- **依赖过重：** **中等。** 39 个包，但均为标准 Python 包，无特殊编译需求
- **过度美股化：** **不存在。** 原生支持 A 股，数据源优先 efinance（东方财富）和 AkShare，中文文档，北京时间调度

---

## 10. 结论

### 立刻可试

- A 股原生支持，300274 直接可用
- 零交易风险，纯分析 + 推送
- 数据源免费（efinance + AkShare）
- 最小运行只需 1 个 LLM Key + 1 个推送渠道
- 39K star，v3.19.0 活跃维护中
- 与 stock-analysis 互补，可同时作为小工坊的每日巡检层

---

## 11. 最小安全试跑方案（建议，不执行）

```
# 1. Clone 到 sandbox
git clone https://github.com/ZhuLinsen/daily_stock_analysis.git \
  /Users/wongdaisy/Mimo-Lab/sandbox/daily_stock_analysis

# 2. 创建独立 venv
cd /Users/wongdaisy/Mimo-Lab/sandbox/daily_stock_analysis
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 最小配置 .env（仅填必要变量）
# STOCK_LIST=300274
# 选择一个 LLM Key（如 Anspire 含免费额度，或 Ollama 本地）
# 不配置任何推送渠道（报告只输出到终端）

# 5. 干跑测试
python main.py --dry-run

# 6. 正式运行（单次，不调度）
python main.py --stocks 300274

# 7. 如果想看 Web 工作台
python main.py --webui --stocks 300274
# 浏览器打开 http://127.0.0.1:8000
```

### 安全边界

- 不配置推送渠道 → 报告不会发送到任何外部平台
- 不启用 Agent → 不触发策略问答
- 不启用事件监控 → 不触发告警
- `--dry-run` 先验证配置，再正式运行
- 仅分析 1 只股票（300274），最小化 API 调用

---

## 附录：配置变量规模

总计约 170+ 个配置变量，覆盖：

- 股票数据源优先级（7 个源）
- AI 模型（15+ 厂商模板）
- 搜索引擎（6 种）
- 通知渠道（11 种）
- Agent 策略（15 种内置策略）
- 回测、调度、WebUI、数据库优化及风险管理

所有变量均为可选（除 STOCK_LIST 和至少 1 个 LLM Key 外），默认值合理，可按需逐步开启。
