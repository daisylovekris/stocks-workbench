# cinar/indicator 只读可用性评估｜2026-06-04

> 评估范围：只读公开 README 与项目结构，不 clone、不安装、不运行。
> 评估目标：判断该工具对股票小工坊的可用性与借鉴价值。
> 评估时间：2026-06-04

---

## 一、核心功能

cinar/indicator 是一个 Go 语言技术指标库，核心功能：

- 50+ 技术指标（趋势/动量/波动率/成交量）
- 15+ 内置策略（可直接回测）
- 策略组合框架（AllStrategies / SeparateStrategies / RunStrategies）
- 简单回测支持（ApplyActions / NormalizeGains / CountTransactions）
- 纯 Go 实现，无外部依赖
- MIT License
- 另有 TypeScript 版本：github.com/cinar/indicatorts

---

## 二、支持的技术指标

### 趋势类指标（Trend）

| 指标 | 函数 | 说明 |
|------|------|------|
| **SMA** | `Sma(period, values)` | 简单移动平均线 |
| **EMA** | `Ema(period, values)` | 指数移动平均线 |
| **RMA** | `Rma(period, values)` | 滚动移动平均线 |
| **DEMA** | `Dema(period, values)` | 双重 EMA |
| **TEMA** | `Tema(period, values)` | 三重 EMA |
| **TRIMA** | `Trima(period, values)` | 三角移动平均 |
| **VWMA** | `Vwma(period, closing, volume)` | 成交量加权移动平均 |
| **MACD** | `Macd(closing)` | 返回 macd + signal |
| **KDJ** | `Kdj(rPeriod, kPeriod, dPeriod, high, low, closing)` | 返回 K/D/J |
| **Parabolic SAR** | `ParabolicSar(high, low, closing)` | 返回 psar + trend |
| **Aroon** | `Aroon(high, low)` | 返回 aroonUp + aroonDown |
| **CCI** | `CommunityChannelIndex(period, high, low, closing)` | 商品通道指数 |
| **Vortex** | `Vortex(high, low, closing)` | 返回 +VI + -VI |
| **TRIX** | `Trix(period, values)` | 三重指数平均 |
| **Mass Index** | `MassIndex(high, low)` | 质量指数 |
| **APO** | `AbsolutePriceOscillator(fastPeriod, slowPeriod, values)` | 绝对价格振荡器 |
| **BOP** | `BalanceOfPower(opening, high, low, closing)` | 力量平衡 |
| **CFO** | `ChandeForecastOscillator(closing)` | 钱德预测振荡器 |
| **Qstick** | `Qstick(period, opening, closing)` | Qstick 指标 |

### 动量类指标（Momentum）

| 指标 | 函数 | 说明 |
|------|------|------|
| **RSI** | `Rsi(closing)` | 返回 rs + rsi |
| **RSI 2** | `Rsi2(closing)` | 2 周期 RSI（Larry Connors） |
| **RSI 自定义周期** | `RsiPeriod(period, closing)` | 自定义周期 RSI |
| **Stochastic** | `StochasticOscillator(high, low, closing)` | 返回 K + D |
| **Williams %R** | `WilliamsR(low, high, closing)` | 威廉指标 |
| **Ichimoku Cloud** | `IchimokuCloud(high, low, closing)` | 返回 5 线：转换/基准/先行A/先行B/滞后 |
| **Awesome Oscillator** | `AwesomeOscillator(low, high)` | 动量振荡器 |
| **Chaikin Oscillator** | `ChaikinOscillator(fastPeriod, slowPeriod, low, high, closing, volume)` | 蔡金振荡器 |
| **PPO** | `PercentagePriceOscillator(...)` | 百分比价格振荡器 |
| **PVO** | `PercentageVolumeOscillator(...)` | 百分比成交量振荡器 |

### 波动率类指标（Volatility）

| 指标 | 函数 | 说明 |
|------|------|------|
| **Bollinger Bands** | `BollingerBands(closing)` | 返回 middle + upper + lower |
| **ATR** | `Atr(period, high, low, closing)` | 返回 tr + atr |
| **Keltner Channel** | `KeltnerChannel(period, high, low, closing)` | 返回 upper + middle + lower |
| **Donchian Channel** | `DonchianChannel(period, closing)` | 返回 upper + middle + lower |
| **Chandelier Exit** | `ChandelierExit(high, low, closing)` | 返回 long + short |
| **Acceleration Bands** | `AccelerationBands(high, low, closing)` | 返回 upper + middle + lower |
| **Ulcer Index** | `UlcerIndex(period, closing)` | 下行风险度量 |
| **Projection Oscillator** | `ProjectionOscillator(period, smooth, high, low, closing)` | 返回 po + spo |

### 成交量类指标（Volume）

| 指标 | 函数 | 说明 |
|------|------|------|
| **OBV** | `Obv(closing, volume)` | 能量潮 |
| **VWAP** | `VolumeWeightedAveragePrice(period, closing, volume)` | 成交量加权平均价 |
| **MFI** | `MoneyFlowIndex(period, high, low, closing, volume)` | 资金流量指标 |
| **CMF** | `ChaikinMoneyFlow(high, low, closing, volume)` | 蔡金资金流 |
| **A/D** | `AccumulationDistribution(high, low, closing, volume)` | 聚散指标 |
| **Force Index** | `ForceIndex(period, closing, volume)` | 力量指数 |
| **EMV** | `EaseOfMovement(period, high, low, volume)` | 简易波动指标 |
| **NVI** | `NegativeVolumeIndex(closing, volume)` | 负成交量指数 |
| **VPT** | `VolumePriceTrend(closing, volume)` | 量价趋势 |

### 回归类（Regression）

| 函数 | 说明 |
|------|------|
| `LeastSquare(x, y)` | 最小二乘法 |
| `MovingLeastSquare(period, x, y)` | 移动最小二乘 |
| `LinearRegressionUsingLeastSquare(values)` | 线性回归 |
| `MovingLinearRegression(period, values)` | 移动线性回归 |

---

## 三、是否支持回测

**支持，但较简单。**

回测函数：

| 函数 | 说明 |
|------|------|
| `NormalizeActions(actions)` | 将原始信号转为 BUY→HOLD→SELL 交替序列 |
| `CountTransactions(actions)` | 统计交易次数 |
| `ApplyActions(prices, actions)` | 按信号计算收益 |
| `NormalizeGains(prices, gains)` | 对比策略收益与买入持有收益 |
| `RunStrategies(asset, strategies...)` | 运行多个策略 |

回测流程：

```
1. 运行策略 → actions
2. 标准化信号 → NormalizeActions
3. 统计交易次数 → CountTransactions
4. 计算收益 → ApplyActions
5. 对比基准 → NormalizeGains（vs BuyAndHold）
```

**局限：** 没有滑点、手续费、资金管理、仓位控制、Monte Carlo 验证等高级回测功能。

---

## 四、是否支持自定义策略

**支持。**

策略类型定义：

```go
type StrategyFunction func(*Asset) []Action
```

可以自定义策略函数，返回 BUY/SELL/HOLD 信号数组。

内置策略组合：

| 组合方式 | 函数 | 说明 |
|---------|------|------|
| 全部一致 | `AllStrategies(strategies...)` | 所有策略都同意时才触发 |
| 分离买卖 | `SeparateStategies(buyStrategy, sellStrategy)` | 买和卖用不同策略 |
| 独立运行 | `RunStrategies(asset, strategies...)` | 多策略独立运行 |

内置复合策略：

- `MacdAndRsiStrategy` — MACD + RSI 组合

---

## 五、输入数据格式

```go
type Asset struct {
    Date    []time.Time
    Opening []float64
    Closing []float64
    High    []float64
    Low     []float64
    Volume  []float64
}
```

标准 OHLCV 格式，与任何市场数据源兼容。

---

## 六、是否适合 A 股日线数据

**适合。**

- 输入是标准 OHLCV `[]float64` 数组，与市场无关
- A 股日线数据（开盘/收盘/最高/最低/成交量）完全匹配
- 无市场特定假设（不像某些库默认美股交易时间）
- 所有指标的计算逻辑是通用的，不依赖特定市场

---

## 七、是否能和已有数据配合

**可以。**

| 数据源 | 格式 | 配合方式 |
|--------|------|---------|
| `data_300274.json` | JSON（含日线 OHLCV） | 解析后转为 `[]float64` 输入 |
| `akshare` | pandas DataFrame | 转为 Go slice 后输入 |
| `mootdx` | pandas DataFrame | 同上 |

配合方式：

```
akshare/mootdx 采集 A 股日线
  → Python 预处理（提取 OHLCV 列）
  → 导出为 CSV/JSON
  → Go 程序读取并计算指标
  → 输出结果
```

或者：

```
用 Python 重写关键指标计算（参考 Go 实现逻辑）
  → 直接在小工坊 Python 环境中使用
```

---

## 八、输出形式

**Go Library，无独立可执行程序。**

- 输出是 `[]float64` 数组（指标值）
- 无终端输出、无图表、无 CSV、无 JSON 导出
- 需要自行编写代码读取结果并格式化
- 可以轻松转为 CSV/JSON/终端输出

---

## 九、是否适合作为股票小工坊的技术指标模块参考

**非常适合。**

| 维度 | 评估 |
|------|------|
| 指标覆盖 | ✅ 非常全面，50+ 指标覆盖小工坊需要的所有常用指标 |
| 计算逻辑 | ✅ 清晰，每个指标有明确公式，可直接参考实现 |
| 策略框架 | ✅ 简洁的 StrategyFunction 接口，可参考其设计 |
| 回测框架 | ⚠️ 较简单，但思路可借鉴（NormalizeActions / ApplyActions） |
| 语言 | ⚠️ Go 语言，小工坊用 Python，需要参考逻辑后用 Python 重写 |
| 数据格式 | ✅ 标准 OHLCV，与 A 股完全兼容 |

---

## 十、对股票小工坊的用途评估

| 用途 | 可行性 | 说明 |
|------|--------|------|
| **5日/10日/20日均线判断** | ✅ 高 | SMA/EMA 函数直接可用（参考实现后用 Python 重写） |
| **MACD / RSI 辅助** | ✅ 高 | `Macd`、`Rsi` 函数完整，公式清晰 |
| **支撑压力辅助** | ✅ 高 | Bollinger Bands / Keltner Channel / Donchian Channel |
| **买回条件验证** | ✅ 高 | RSI < 30 / MACD 金叉 / KDJ 等信号 |
| **反抽质量判断** | ✅ 高 | RSI / MACD / 成交量指标（OBV/MFI/CMF） |
| **简单策略回测参考** | 🟡 中 | 回测框架较简单，但策略组合思路可借鉴 |
| **KDJ 指标** | ✅ 高 | `Kdj` 函数完整，返回 K/D/J |
| **ATR 波动率** | ✅ 高 | `Atr` 函数完整 |
| **成交量分析** | ✅ 高 | OBV / VWAP / MFI / CMF / A/D / Force Index |

---

## 十一、风险点

| 风险 | 等级 | 说明 |
|------|------|------|
| **指标过多导致过拟合** | 🟡 中 | 50+ 指标不是都适合 A 股，需要选择性使用 |
| **偏通用市场，A 股适配未知** | 🟢 低 | OHLCV 通用格式，与 A 股完全兼容，但未专门测试 |
| **技术指标不能替代基本面** | 🟡 中 | 技术指标只是辅助，不能替代财务深研和估值判断 |
| **回测结果可能误导** | 🟡 中 | 回测框架较简单，无滑点/手续费/资金管理 |
| **数据质量依赖外部来源** | 🟡 中 | 指标计算依赖输入数据质量（akshare/mootdx） |
| **Go 语言，改造成本** | 🟡 中 | 小工坊用 Python，需要参考逻辑后重写 |
| **无交易功能** | 🟢 低 | 纯指标计算库，无交易能力，符合小工坊原则 |

---

## 十二、结论

**评级：只读参考 + 可离线试跑指标计算**

理由：

1. **指标覆盖非常全面。** 50+ 技术指标，覆盖小工坊需要的所有常用指标（MA/EMA/MACD/RSI/KDJ/Bollinger/ATR/成交量等）。
2. **计算逻辑清晰可参考。** 每个指标有明确公式和 Go 实现，可直接参考后用 Python 重写。
3. **标准 OHLCV 输入，与 A 股完全兼容。** 无市场特定假设。
4. **Go 语言是唯一障碍。** 小工坊用 Python，需要参考逻辑后重写。但指标计算本身不复杂。
5. **回测框架可借鉴但较简单。** 无滑点/手续费/资金管理，不适合直接用于小工坊回测。
6. **无交易功能，符合小工坊原则。** 纯指标计算库。

建议态度：

- ✅ 参考其指标计算逻辑，用 Python 重写小工坊需要的指标
- ✅ 参考其策略框架设计（StrategyFunction 接口）
- ✅ 参考其回测思路（NormalizeActions / ApplyActions）
- ✅ 可以直接用 Go 跑离线指标计算（如果愿意装 Go 环境）
- ❌ 不需要引入整个库到小工坊
- ❌ 不用于自动交易或实盘信号

---

## 十三、后续试跑方案：离线技术指标计算

**前提：** 只用于离线技术指标计算和历史日线回测参考，不涉及自动交易或实盘信号。

### 方案 A：参考 Go 实现，用 Python 重写关键指标

不需要装 Go 环境，直接参考 Go 代码逻辑，用 Python 实现。

优先重写的指标：

```python
# 基础均线
def sma(period, values): ...
def ema(period, values): ...

# 趋势
def macd(closing): ...          # 返回 macd, signal
def kdj(high, low, closing): ... # 返回 k, d, j

# 动量
def rsi(closing): ...            # 返回 rs, rsi

# 波动率
def bollinger_bands(closing): ... # 返回 middle, upper, lower
def atr(period, high, low, closing): ... # 返回 tr, atr

# 成交量
def obv(closing, volume): ...
def mfi(period, high, low, closing, volume): ...
```

### 方案 B：Go 离线计算（如果装 Go 环境）

```bash
# 安装
go get github.com/cinar/indicator

# 编写 Go 程序读取 data_300274.json，计算指标，输出 CSV
```

### 方案 C：参考 akshare 内置技术指标

akshare 本身已提供部分技术指标接口，可能不需要额外引入。

### 禁止事项

- ❌ 不用于自动交易
- ❌ 不用于实盘信号
- ❌ 不接入券商
- ❌ 不生成买卖建议
- ❌ 不将回测结果直接用于操作决策

---

## 附录：项目关键数据

| 项目 | 数据 |
|------|------|
| 仓库 | https://github.com/cinar/indicator |
| License | MIT |
| 语言 | Go（另有 TypeScript 版：github.com/cinar/indicatorts） |
| 技术指标 | 50+（趋势/动量/波动率/成交量/回归） |
| 内置策略 | 15+（趋势/动量/波动率/成交量/复合） |
| 回测支持 | ✅ 基础（ApplyActions / NormalizeGains） |
| 输入格式 | 标准 OHLCV `[]float64` |
| 输出格式 | Go Library（`[]float64` 数组） |
| 外部依赖 | 无 |
| A 股兼容 | ✅ OHLCV 通用格式，与 A 股完全兼容 |
| 交易功能 | ❌ 无 |
