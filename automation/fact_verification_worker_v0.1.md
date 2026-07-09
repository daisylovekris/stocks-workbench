# Fact Verification Worker v0.1

## 1. 定位

`fetch_daily_quote` / AkShare 主抓取负责生成主 facts candidate。

Fact Verification Worker 负责字段级第二来源复核：

- 不直接改主 facts
- 不判断“是否修复完成 / 是否风险解除 / 是否底部确认 / 是否适合加仓”
- 只输出 verification 状态
- 只在字段级做补证、确认、冲突识别

它的职责是把“候选值”变成“可合并 / 需人工 / 冲突”。

## 2. 为什么需要它

这次 2026-07-07 / 2026-07-08 阳光电源 facts pack 的回填，暴露了几个问题：

- `volume_ratio` 候选值会串到别的交易日
- `pct_change` 需要按 `close / prev_close` 二次核验
- 人工核对能解决一次，但不适合每次都手工重复
- 需要把“需要补证、需要确认、需要仲裁”的字段自动化

目标不是替代人，而是把字段级核验流程标准化。

## 3. 两段式流程

1. 主抓取脚本生成 facts pack candidate
2. 自动生成 review manifest
3. fact verification worker 按字段模板搜索第二来源
4. 输出 `verification.json`
5. merge / validator 决定哪些字段能进主 facts
6. review generation 只使用 confirmed 或明确标注状态的字段

## 4. 输入

输入包括：

- facts pack
- review manifest
- allowed source whitelist
- field-level query templates
- target date
- stock code / stock name
- expected fields

## 5. 输出

worker 只输出 verification 结果，不直接写主 facts。

建议 schema 示例：

```json
{
  "field": "volume_ratio",
  "target_date": "2026-07-08",
  "candidate_value": 1.19,
  "verified_value": 0.55,
  "status": "conflict",
  "confidence": "high",
  "source_name": "agent_search",
  "source_url": null,
  "source_date": "2026-07-08",
  "retrieved_at": null,
  "evidence_excerpt": null,
  "note": "Candidate appears to match another/current trading day and must not be used for target date."
}
```

状态枚举：

- `candidate`
- `confirmed`
- `conflict`
- `needs_manual_check`
- `rejected`

## 6. 字段分工

适合自动复核：

- `volume_ratio`
- `pct_change` 二次反算
- `prev_close` 基准
- 新增公告是否存在
- 新闻是否有明确来源
- 板块红绿
- 外部政策消息是否有证据

不允许 worker 直接定性：

- 是否修复完成
- 是否风险解除
- 是否底部确认
- 是否支撑成立
- 是否适合加仓
- 是否应该买卖

## 7. 白名单来源与查询模板

原则：

- 不允许开放式自由搜索
- 每个字段必须有 allowed source whitelist
- 每个字段必须有 query template
- 每个 verification 必须记录 source / date / evidence / confidence

示例：

### volume_ratio

- query: `阳光电源 300274 2026-07-08 量比`
- required evidence: 股票名或代码 + 日期 + 量比数值
- acceptance: same target_date + numeric match + allowed source

### disclosure_status

- query: `阳光电源 300274 2026-07-08 公告`
- required evidence: 公告标题 + 发布日期 + 链接
- acceptance: 官方交易所 / 巨潮 / 公司披露页优先

## 8. 合并规则

- `confirmed + same_date + allowed_source` 才能进入主 facts
- `conflict` 不覆盖主 facts，只写 verification
- `needs_manual_check` 保留人工复核
- `candidate` 不能进入复盘主链
- validator 应阻止未确认字段被写成确认性结论

## 9. 与 validator 的关系

- validator 不负责联网
- validator 只读取 facts pack / verification 状态
- `R006` 继续保护 disclosure/news/policy 未确认时不能写“无新增重大利好/利空”
- 后续可以增加字段级 consistency check，例如 `pct_change` 是否等于 `close/prev_close` 反算值

## 10. 下一步

- 设计 `review_manifest` schema
- 设计 `verification.json` schema
- 为 `volume_ratio` / `pct_change` / `disclosure_status` 先做 3 个字段模板
- 增加 facts merge 规则
- 增加 validator consistency check：`pct_change` 与 `close/prev_close` 不一致时报警
- 收盘后自动抓当日数据，减少历史回填误差
