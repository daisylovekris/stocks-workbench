"""
A 股复盘行情取数通道 v0.1

用途：
- 用 AKShare 查询 A 股日线数据
- 与同花顺人工数据做字段对比
- 只在终端打印结果，不写入任何文件
- 不做交易，不生成买卖建议

数据源口径：
- AKShare 只作为自动源候选
- 同花顺人工数据仍是当前可信基准
- 本脚本只读查询，不做交易
"""

import argparse
from datetime import datetime


# 同花顺人工基准数据
THS_BENCHMARK = {
    "日期": "2026-06-09",
    "开盘": 149.44,
    "最高": 153.30,
    "最低": 144.57,
    "收盘": 152.50,
    "涨跌幅": 3.88,
    "成交额": 89.91,  # 亿元
    "换手率": 3.8,
}

# 对比容差
TOLERANCE = {
    "价格": 0.02,
    "涨跌幅": 0.05,
    "成交额": 0.20,  # 亿元
    "换手率": 0.05,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="A 股复盘行情取数通道 v0.1 — AKShare 只读查询与同花顺对比"
    )
    parser.add_argument("--symbol", default="300274", help="股票代码，默认 300274")
    parser.add_argument("--date", default="2026-06-09", help="查询日期，默认 2026-06-09")
    parser.add_argument("--period", default="daily", help="周期，默认 daily")
    parser.add_argument("--adjust", default="", help="复权类型，默认空字符串")
    return parser.parse_args()


def check_field(name, ths_value, ak_value, tolerance, unit=""):
    """对比单个字段，返回 (差异, 是否通过)"""
    if ak_value is None:
        return "字段缺失", False
    diff = abs(ak_value - ths_value)
    passed = diff <= tolerance
    diff_str = f"{diff:.2f}{unit}"
    return diff_str, passed


def main():
    args = parse_args()

    print("=" * 60)
    print("A 股复盘行情取数通道 v0.1")
    print("=" * 60)
    print(f"标的: {args.symbol}")
    print(f"日期: {args.date}")
    print(f"周期: {args.period}")
    print(f"复权: {args.adjust if args.adjust else '不复权'}")
    print()

    # 导入 akshare
    try:
        import akshare as ak
    except ImportError:
        print("akshare 未安装。当前脚本不会自动安装依赖。请人工确认后再决定是否安装。")
        return

    # 准备查询参数
    date_str = args.date.replace("-", "")
    try:
        df = ak.stock_zh_a_hist(
            symbol=args.symbol,
            period=args.period,
            start_date=date_str,
            end_date=date_str,
            adjust=args.adjust,
        )
    except Exception as e:
        print(f"查询出错: {e}")
        return

    # 打印原始列名
    print(f"AKShare 返回列名: {list(df.columns)}")
    print()

    # 检查是否查到数据
    if df.empty:
        print("未查询到该日期数据，请检查交易日、symbol 或数据源。")
        return

    # 取第一行数据
    row = df.iloc[0]

    # 提取字段
    ak_date = str(row.get("日期", ""))
    ak_open = float(row["开盘"]) if "开盘" in row.index else None
    ak_high = float(row["最高"]) if "最高" in row.index else None
    ak_low = float(row["最低"]) if "最低" in row.index else None
    ak_close = float(row["收盘"]) if "收盘" in row.index else None
    ak_pct = float(row["涨跌幅"]) if "涨跌幅" in row.index else None
    ak_turnover = float(row["换手率"]) if "换手率" in row.index else None

    # 成交额处理
    ak_amount = None
    if "成交额" in row.index:
        ak_amount_raw = float(row["成交额"])
        # AKShare 成交额通常为元，转换为亿元
        ak_amount = ak_amount_raw / 1e8
    elif "amount" in row.index:
        ak_amount_raw = float(row["amount"])
        ak_amount = ak_amount_raw / 1e8

    # 打印 AKShare 原始数据
    print("AKShare 查询结果:")
    print(f"  日期:    {ak_date}")
    print(f"  开盘:    {ak_open}")
    print(f"  最高:    {ak_high}")
    print(f"  最低:    {ak_low}")
    print(f"  收盘:    {ak_close}")
    print(f"  涨跌幅:  {ak_pct}")
    print(f"  成交额:  {ak_amount:.2f} 亿" if ak_amount else "  成交额:  字段缺失")
    print(f"  换手率:  {ak_turnover}")
    print()

    # 与同花顺对比
    print("字段对比:")
    print("-" * 60)
    print(f"{'字段':<8} {'同花顺':>10} {'AKShare':>10} {'差异':>10} {'结果':>6}")
    print("-" * 60)

    fields = [
        ("开盘", THS_BENCHMARK["开盘"], ak_open, TOLERANCE["价格"], ""),
        ("最高", THS_BENCHMARK["最高"], ak_high, TOLERANCE["价格"], ""),
        ("最低", THS_BENCHMARK["最低"], ak_low, TOLERANCE["价格"], ""),
        ("收盘", THS_BENCHMARK["收盘"], ak_close, TOLERANCE["价格"], ""),
        ("涨跌幅", THS_BENCHMARK["涨跌幅"], ak_pct, TOLERANCE["涨跌幅"], ""),
        ("成交额", THS_BENCHMARK["成交额"], ak_amount, TOLERANCE["成交额"], "亿"),
        ("换手率", THS_BENCHMARK["换手率"], ak_turnover, TOLERANCE["换手率"], ""),
    ]

    all_passed = True
    missing_fields = False

    for name, ths_val, ak_val, tol, unit in fields:
        if ak_val is None:
            diff_str = "字段缺失"
            passed = False
            missing_fields = True
        else:
            diff_str, passed = check_field(name, ths_val, ak_val, tol, unit)

        if not passed:
            all_passed = False

        ths_str = f"{ths_val:.2f}"
        ak_str = f"{ak_val:.2f}" if ak_val is not None else "缺失"
        result_str = "通过" if passed else "不通过"

        print(f"{name:<8} {ths_str:>10} {ak_str:>10} {diff_str:>10} {result_str:>6}")

    print("-" * 60)
    print()

    # 输出结论
    if missing_fields:
        print("结论：AKShare 字段不完整，需要继续校验。")
    elif all_passed:
        print("结论：AKShare 与同花顺人工口径基本一致，可作为自动行情源候选。")
    else:
        print("结论：AKShare 与同花顺存在差异，暂不自动替代人工口径。")

    print()
    print("注：量比不在此对比中，因为 AKShare 日线通常不提供量比字段。")


if __name__ == "__main__":
    main()
