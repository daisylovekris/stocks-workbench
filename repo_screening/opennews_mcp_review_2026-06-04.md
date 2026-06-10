# 6551Team/opennews-mcp 只读可用性评估｜2026-06-04

> 评估范围：只读公开 README 与项目结构，不 clone、不安装、不运行。
> 评估目标：判断该工具对股票小工坊的可用性与借鉴价值。
> 评估时间：2026-06-04

---

## 一、核心功能

opennews-mcp 是一个基于 MCP 协议的新闻聚合服务器，核心功能：

- 84+ 实时数据源，跨 6 大引擎类别
- AI 分析每篇文章，产出 impact score（0—100）、trading signal（long/short/neutral）、grade（A+—C）
- 中英双语摘要
- 全文关键词搜索
- 按币种、来源、引擎类型、AI 评分、交易信号筛选
- WebSocket 实时推送
- 多条件高级搜索（币种 + 关键词 + 引擎类型组合）

---

## 二、新闻来源（84+，6 大类别）

### 1. News（53 个来源，engineType: "news"）

主流财经媒体、政府机构、社交平台：

| 类型 | 来源 |
|------|------|
| 主流财经 | Bloomberg、Reuters、Financial Times、CNBC、CNN、BBC、Fox Business、Business Insider |
| 加密媒体 | CoinDesk、Cointelegraph、The Block、Blockworks、Decrypt、DlNews |
| 科技媒体 | TechCrunch、Wired、The Verge、Medium、Techinasia |
| 政府/宏观 | U.S. Treasury、U.S. Trade Representative、ECB、TASS、Interfax、Politico |
| 欧洲媒体 | Handelsblatt、Welt、Telegraph |
| 机构 | MS NOW（Morgan Stanley）、Ambrey（海事情报） |
| 社交 | Twitter/X、Telegram、Weibo、Truth Social |
| 公关/公告 | PR Newswire、Coinbase、Binance |
| 中文源 | **Jin10（金十数据）** |
| 加密专用 | Crypto Narratives、Crypto in America、6551News、BWEnews、AGGRNEWS、Velo |

### 2. Listing（9 个来源，engineType: "listing"）

交易所上币公告：Binance、Coinbase、OKX、Bybit、Upbit、Bithumb、Robinhood、Hyperliquid、Aster

### 3. OnChain（3 个来源，engineType: "onchain"）

Hyperliquid 鲸鱼交易、大额持仓、KOL 交易

### 4. Meme（1 个来源，engineType: "meme"）

Twitter/X meme 币讨论

### 5. Market（6 个来源，engineType: "market"）

价格变动、资金费率、大额清算、市场趋势、持仓量变化

### 6. Prediction（12 个来源，engineType: "prediction"）

AI 预测信号：相关性逻辑、聪明钱交易、价格飙升、集群入场、鲸鱼持仓、新钱包交易、内幕模式等

---

## 三、是否支持财经/股票/公司公告/行业新闻

**部分支持，但以加密货币为主。**

| 维度 | 支持情况 |
|------|---------|
| 财经新闻 | ✅ Bloomberg、Reuters、FT、CNBC 等主流财经媒体 |
| 宏观/政策 | ✅ U.S. Treasury、ECB、TASS、Politico 等 |
| 加密货币 | ✅ 核心目标市场，6 大引擎全部围绕加密 |
| A 股公司公告 | ❌ 不支持，无 A 股公告源 |
| A 股行业新闻 | ❌ 不支持 |
| 美股个股 | ⚠️ 有主流财经媒体覆盖，但无美股个股专门筛选 |
| 中文财经 | ⚠️ 仅有 Jin10（金十数据），覆盖面有限 |

---

## 四、是否适合 A 股盘前消息检查

**不适合。**

原因：

1. 84+ 数据源中没有 A 股公告源（巨潮资讯、上交所、深交所、东方财富公告等）
2. 没有 A 股个股筛选能力（不支持按 300274.SZ 等代码搜索）
3. AI 评级和 trading signal 是针对加密货币设计的（long/short/neutral）
4. 币种筛选用的是 BTC、ETH、SOL 等加密符号，不是股票代码
5. Jin10 是唯一中文源，但主要覆盖宏观和加密，不覆盖 A 股个股公告

**但可以用于：**

- 外围宏观/政策消息检查（美联储、ECB、贸易政策）
- 地缘政治风险监测（TASS、Ambrey）
- 全球财经大事件感知（Bloomberg、Reuters 头条）

---

## 五、是否能只作为新闻线索源

**可以。该项目本身没有交易/下单功能。**

- 只产出新闻、AI 评级、trading signal
- 没有券商连接器
- 没有下单能力
- 是纯信息聚合 + AI 分析工具

但 trading signal（long/short/neutral）是高风险输出，需要谨慎对待。

---

## 六、是否有高风险模块

| 模块 | 风险等级 | 说明 |
|------|---------|------|
| **AI 评级（0—100 score）** | 🔴 高 | LLM 生成的影响力评分，可能过度自信或误导 |
| **Trading Signal（long/short/neutral）** | 🔴 高 | AI 生成的方向性信号，容易被误用为交易依据 |
| **Grade（A+—C）** | 🟡 中 | 分级评价，可能给人虚假的确定感 |
| **Prediction 引擎** | 🔴 高 | 12 种 AI 预测信号（鲸鱼持仓、内幕模式等），高度投机性 |
| **Meme 引擎** | 🟡 中 | Meme 币讨论追踪，投机性强 |

**关键风险：** 这些 AI 评级和信号看起来很专业，但本质是 LLM 输出，存在幻觉和过度自信风险。不能作为交易依据。

---

## 七、输出形式

### MCP Tool Response（JSON）

```json
{
  "id": "unique-article-id",
  "text": "标题 / 内容",
  "newsType": "Bloomberg",
  "engineType": "news",
  "link": "https://...",
  "coins": [
    {
      "symbol": "BTC",
      "market_type": "cex",
      "score": 85,
      "signal": "long",
      "grade": "A"
    }
  ],
  "aiRating": {
    "score": 85,
    "grade": "A",
    "signal": "long",
    "summary": "中文摘要",
    "enSummary": "English summary"
  },
  "ts": 1708473600000
}
```

### WebSocket 推送

- `news.update`：新文章推送
- `news.ai_update`：AI 分析完成更新
- `strategy.triggered`：策略触发事件

### 无其他输出形式

不支持 Markdown、HTML、图片、报告等格式。

---

## 八、是否需要 API Key

**是的，必须配置。**

| 配置项 | 说明 |
|--------|------|
| `OPENNEWS_TOKEN` | 必须，从 https://6551.io/mcp 获取 |
| `OPENNEWS_API_BASE` | 可选，覆盖 REST API 地址 |
| `OPENNEWS_WSS_URL` | 可选，覆盖 WebSocket 地址 |
| `OPENNEWS_MAX_ROWS` | 可选，每次请求最大结果数（默认 100） |

Token 获取方式：访问 https://6551.io/mcp 注册获取。

---

## 九、对股票小工坊的用途评估

| 用途 | 可行性 | 说明 |
|------|--------|------|
| **盘前消息检查** | 🔴 低 | 不支持 A 股个股公告，仅覆盖宏观/加密 |
| **个股突发新闻** | 🔴 低 | 无法按 A 股代码搜索 |
| **行业催化** | 🟡 中 | 主流财经媒体可覆盖部分行业大事件 |
| **外围影响** | 🟡 中 | 美联储、ECB、贸易政策、地缘政治有覆盖 |
| **新闻源交叉验证** | 🟡 中 | 84+ 来源可用于宏观/外围消息的多源验证 |
| **A 股专用新闻源** | 🔴 低 | 不支持 A 股 |
| **MCP 协议参考** | 🟡 中 | MCP server 实现可参考，但小工坊已有类似能力 |

---

## 十、风险点

| 风险 | 等级 | 说明 |
|------|------|------|
| **新闻源质量不明** | 🟡 中 | 84+ 来源质量参差不齐，meme/prediction 来源可靠性低 |
| **AI 评级幻觉** | 🔴 高 | 0—100 评分、A+—C 分级、long/short/neutral 信号均为 LLM 生成，存在幻觉 |
| **过度依赖情绪信号** | 🔴 高 | Trading signal 看起来很精确，但本质是概率性 LLM 输出 |
| **A 股覆盖不足** | 🔴 高 | 核心面向加密市场，A 股几乎无覆盖 |
| **API Token 风险** | 🟡 中 | 需要从 6551.io 获取 token，存在第三方依赖 |
| **加密市场偏向** | 🔴 高 | 6 大引擎全部围绕加密设计，不适用于 A 股 |
| **Prediction 引擎投机性** | 🔴 高 | 12 种 AI 预测信号（鲸鱼、内幕模式等）高度投机 |
| **MCP 权限边界** | 🟢 低 | 只读新闻检索，无写入/交易能力 |

---

## 十一、结论

**评级：暂不建议碰**

理由：

1. **核心面向加密市场。** 84+ 数据源中绝大多数是加密媒体、交易所上币、链上数据、meme 币讨论。6 大引擎全部围绕加密设计。
2. **A 股几乎无覆盖。** 没有 A 股公告源、没有 A 股个股筛选、没有 A 股行业新闻。唯一中文源 Jin10 主要覆盖宏观和加密。
3. **AI 评级和 Trading Signal 是高风险模块。** LLM 生成的 0—100 评分、A+—C 分级、long/short/neutral 信号，容易被误用为交易依据。
4. **需要第三方 API Token。** 依赖 6551.io 的 token，存在第三方服务依赖。
5. **对小工坊价值有限。** 无法用于盘前消息检查、个股突发新闻、A 股行业催化等核心需求。

唯一有价值的部分：

- Bloomberg、Reuters、FT、CNBC 等主流财经媒体的宏观新闻
- 美联储、ECB、贸易政策等外围消息
- MCP server 实现的技术参考

但这些价值不值得引入一个加密偏向 + AI 评级幻觉风险的系统。

建议态度：

- ❌ 不用于 A 股分析
- ❌ 不用于盘前消息检查
- ❌ 不用于个股新闻
- ❌ 不引入其 AI 评级和 Trading Signal
- ⚠️ 如果未来做加密市场研究，可以重新评估
- ⚠️ MCP server 实现可作为技术参考，但不需要专门引入

---

## 十二、不建议试跑

由于该项目核心面向加密市场，A 股覆盖几乎为零，且 AI 评级和 Trading Signal 存在高风险，不建议后续试跑。

如果未来需要宏观/外围新闻源，建议：

1. 优先使用 Perplexity 交叉验证（已在小工坊流程中）
2. 优先使用 Jin10 金十数据直接访问（不通过 opennews-mcp）
3. 优先使用 Bloomberg/Reuters RSS 或 API（如果有渠道）

不需要通过 opennews-mcp 引入一个加密偏向的新闻聚合层。

---

## 附录：项目关键数据

| 项目 | 数据 |
|------|------|
| 仓库 | https://github.com/6551Team/opennews-mcp |
| License | MIT |
| 语言 | Python |
| 数据源 | 84+（6 大引擎类别） |
| 核心市场 | 加密货币 |
| A 股支持 | ❌ 不支持 |
| AI 功能 | impact score（0—100）、trading signal（long/short/neutral）、grade（A+—C）、中英摘要 |
| 输出形式 | MCP tool response（JSON）+ WebSocket 推送 |
| API Token | 必须，从 6551.io 获取 |
| 交易功能 | ❌ 无 |
| 部署方式 | MCP server（stdio），支持 Claude Code/Desktop/Cursor/Windsurf/Cline 等 |
