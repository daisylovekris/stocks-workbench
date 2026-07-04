"""
A 股复盘行情取数通道 v0.1

用途：
- 用腾讯行情作为主数据源查询 A 股日线数据
- 东方财富仅作为 optional diagnostic source，失败不中断主流程
- 与同花顺人工数据做字段对比
- 只在终端打印结果，不写入任何文件
- 不做交易，不生成买卖建议

数据源口径：
- 腾讯行情：默认主数据源（通过 AKShare stock_zh_a_daily 接口）
- 东方财富：optional diagnostic source（通过 AKShare stock_zh_a_hist 接口），失败不影响主流程
- 同花顺人工数据仍是当前可信基准
- 本脚本只读查询，不做交易
"""

import argparse
import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# 同花顺人工基准数据
THS_BENCHMARK = {
    # 当前人工基准对应 2026-07-03；后续每日复盘若切换日期，需同步更新这里
    "日期": "2026-07-03",
    "股票代码": "300274",
    "股票名称": "阳光电源",
    "开盘": 127.80,
    "最高": 131.46,
    "最低": 126.10,
    "收盘": 126.16,
    "昨收": 127.84,
    "涨跌幅": -1.31,
    "成交额": 73.68,  # 亿元
    "换手率": 3.62,
    "振幅": 4.19,
    "成交量": 57446827,  # 股
    "成交量_手": 574468,
    "量比": 0.59,
}

# 对比容差
TOLERANCE = {
    "价格": 0.02,
    "涨跌幅": 0.05,
    "成交额": 0.20,  # 亿元
    "换手率": 0.05,
}

# 腾讯行情字段映射说明（通过 AKShare stock_zh_a_daily 接口获取）
# 该接口底层数据源为腾讯财经（finance.qq.com）
# 返回列名为英文：date, open, high, low, close, volume, amount, outstanding_share, turnover
# 字段含义：
#   date              → 日期
#   open              → 开盘价
#   high              → 最高价
#   low               → 最低价
#   close             → 收盘价
#   volume            → 成交量（股）
#   amount            → 成交额（元，脚本内转换为亿元）
#   outstanding_share → 流通股本
#   turnover          → 换手率（%）
# 注意：腾讯日线接口不提供原始涨跌幅和量比字段；涨跌幅应优先由收盘/昨收计算，量比仍由候选源交叉验证
TENCENT_FIELD_MAP = {
    "日期": "date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
    "成交额": "amount",
    "换手率": "turnover",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="A 股复盘行情取数通道 v0.1 — 腾讯行情主数据源，东方财富 diagnostic"
    )
    parser.add_argument("--symbol", default="300274", help="股票代码，默认 300274")
    parser.add_argument("--date", default=THS_BENCHMARK["日期"], help="查询日期，默认当前人工基准日期")
    parser.add_argument("--period", default="daily", help="周期，默认 daily")
    parser.add_argument("--adjust", default="", help="复权类型，默认空字符串")
    return parser.parse_args()


def check_field(name, ths_value, src_value, tolerance, unit=""):
    """对比单个字段，返回 (差异, 是否通过)"""
    if src_value is None or ths_value is None:
        return "字段缺失", False
    diff = abs(src_value - ths_value)
    passed = diff <= tolerance
    diff_str = f"{diff:.2f}{unit}"
    return diff_str, passed


def _safe_float(value):
    """尽量把字符串 / 数值转成浮点数；失败返回 None。"""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _http_get_text(url, params=None, timeout=10):
    """读取文本响应，保持为只读的最小网络 helper。"""
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _tencent_symbol_prefix(symbol):
    return "sz" if symbol.startswith(("3", "0")) else "sh"


def parse_total(raw):
    """安全解析分页 total；支持 int 和纯数字字符串，失败返回 None。"""
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if raw.isdigit():
            return int(raw)
    return None


def _derive_pct_change(close_value, prev_close_value):
    """由收盘价 / 昨收计算涨跌幅（%）；无法计算时返回 None。"""
    if close_value is None or prev_close_value in (None, 0):
        return None
    return ((close_value - prev_close_value) / prev_close_value) * 100


def get_tencent_realtime_volume_ratio(symbol: str) -> dict:
    """
    腾讯实时 / quote 量比候选获取。

    优先使用腾讯排行接口 JSON 的 lb 字段，再用 qt.gtimg.cn 原始快照做交叉验证。
    返回值仅用于 diagnostic，不进入正式主链字段。
    """
    tencent_code = f"{_tencent_symbol_prefix(symbol)}{symbol}"
    result = {
        "status": "量比候选缺失",
        "candidate_value": None,
        "primary_source": None,
        "board_rank_lb": None,
        "qt_index_49_lb": None,
        "board_rank_raw": None,
        "qt_raw_fragment": None,
        "message": "量比候选缺失",
    }

    board_rank_url = "https://proxy.finance.qq.com/cgi/cgi-bin/rank/hs/getBoardRankList"
    board_rank_error = None
    page_size = 200
    safety_cap = 100
    total_pages = None
    page = 0
    while page < safety_cap:
        params = {
            "_appver": "11.17.0",
            "board_code": "aStock",
            "sort_type": "price",
            "direct": "down",
            "offset": str(page * page_size),
            "count": str(page_size),
        }
        try:
            board_text = _http_get_text(board_rank_url, params=params, timeout=15)
            board_json = json.loads(board_text)
        except Exception as exc:  # noqa: BLE001
            board_rank_error = f"腾讯排行接口读取失败: {exc}"
            break

        if board_json.get("code") != 0 or "data" not in board_json:
            board_rank_error = f"腾讯排行接口返回异常: {board_json.get('msg', 'unknown')}"
            break

        board_data = board_json["data"]
        rows = board_data.get("rank_list", [])
        matched_row = None
        for row in rows:
            if row.get("code") == tencent_code:
                matched_row = row
                break
        if matched_row is not None:
            board_lb = _safe_float(matched_row.get("lb"))
            result["board_rank_lb"] = board_lb
            result["board_rank_raw"] = matched_row
            if board_lb is not None:
                result["primary_source"] = "腾讯排行接口 lb"
            break

        if total_pages is None:
            total_raw = board_data.get("total")
            total_count = parse_total(total_raw)
            if total_count is not None and total_count > 0:
                total_pages = (total_count + page_size - 1) // page_size

        if total_pages is not None:
            page += 1
            if page >= total_pages:
                break
            continue

        if not rows or len(rows) < page_size:
            break

        page += 1

    qt_lb = None
    qt_fragment = None
    try:
        qt_text = _http_get_text(f"https://qt.gtimg.cn/q={tencent_code}", timeout=15)
        qt_payload = qt_text.split("=", 1)[1].strip().strip('";')
        qt_parts = qt_payload.split("~")
        if len(qt_parts) > 49:
            qt_lb = _safe_float(qt_parts[49])
            qt_fragment = "~".join(qt_parts[47:52])
    except Exception as exc:  # noqa: BLE001
        qt_fragment = f"qt 读取失败: {exc}"

    result["qt_index_49_lb"] = qt_lb
    result["qt_raw_fragment"] = qt_fragment

    board_lb = result["board_rank_lb"]
    if board_lb is None and qt_lb is None:
        if board_rank_error:
            result["message"] = f"量比候选缺失；{board_rank_error}"
        else:
            result["message"] = "量比候选缺失"
        return result

    if board_lb is not None and qt_lb is not None:
        if abs(board_lb - qt_lb) <= 0.05:
            result["candidate_value"] = board_lb
            result["primary_source"] = "腾讯排行接口 lb"
            result["status"] = "候选量比与交叉验证一致"
            result["message"] = "候选量比与交叉验证一致，仍需同花顺人工核对"
            return result
        result["status"] = "字段解析异常，不入主链"
        result["message"] = (
            f"字段解析异常，不入主链；腾讯排行 lb={board_lb:.2f}，qt index 49={qt_lb:.2f}"
        )
        return result

    if board_lb is not None:
        result["candidate_value"] = board_lb
        result["status"] = "候选量比可用"
        result["message"] = "腾讯排行接口 lb 可用，仍需同花顺人工核对"
        return result

    result["candidate_value"] = qt_lb
    result["primary_source"] = "qt.gtimg.cn index 49"
    result["status"] = "候选量比可用"
    result["message"] = "腾讯排行接口 lb 缺失，已退回 qt 快照候选，仍需同花顺人工核对"
    return result


def fetch_tencent_data(ak, symbol, date_str, adjust):
    """
    从腾讯行情获取日线数据（通过 AKShare stock_zh_a_daily 接口）。
    返回 (data_dict, error_msg)。
    成功时 error_msg 为 None；失败时 data_dict 为 None。

    字段来源：腾讯财经（finance.qq.com），通过 AKShare stock_zh_a_daily 接口。
    返回列名为英文：date, open, high, low, close, volume, amount, outstanding_share, turnover。
    涨跌幅和量比不在返回列中。
    """
    try:
        df = ak.stock_zh_a_daily(
            symbol=f"{_tencent_symbol_prefix(symbol)}{symbol}",
            start_date=date_str,
            end_date=date_str,
            adjust=adjust if adjust else "",
        )
    except Exception as e:
        return None, f"接口调用异常: {e}"

    if df is None or df.empty:
        return None, "未查询到该日期数据（可能非交易日或 symbol 有误）"

    row = df.iloc[0]
    cols = list(df.columns)

    data = {"列名": cols}

    # 日期：优先英文列名 date，回退中文 日期
    data["日期"] = str(row.get("date", row.get("日期", "")))

    # 价格字段：开盘(open)、最高(high)、最低(low)、收盘(close)
    price_map = {"开盘": "open", "最高": "high", "最低": "low", "收盘": "close"}
    for cn_name, en_name in price_map.items():
        if en_name in row.index:
            data[cn_name] = float(row[en_name])
        elif cn_name in row.index:
            data[cn_name] = float(row[cn_name])
        else:
            data[cn_name] = None

    # 涨跌幅：腾讯日线接口不提供原始值，先标记为 None，后续可由收盘 / 昨收派生
    data["涨跌幅"] = None

    # 换手率：turnover（英文）或 换手率（中文回退）
    # 注意：腾讯返回的 turnover 为小数形式（如 0.038 表示 3.8%），需乘以 100 转换为百分比
    if "turnover" in row.index:
        data["换手率"] = float(row["turnover"]) * 100
    elif "换手率" in row.index:
        data["换手率"] = float(row["换手率"])
    else:
        data["换手率"] = None

    # 成交额：amount（英文，元→亿元）或 成交额（中文回退）
    if "amount" in row.index:
        data["成交额"] = float(row["amount"]) / 1e8
    elif "成交额" in row.index:
        data["成交额"] = float(row["成交额"]) / 1e8
    else:
        data["成交额"] = None

    return data, None


def fetch_eastmoney_data(ak, symbol, date_str, period, adjust):
    """
    从东方财富获取日线数据（通过 AKShare stock_zh_a_hist 接口）。
    仅作为 optional diagnostic source，失败不影响主流程。
    返回 (data_dict, error_msg)。
    成功时 error_msg 为 None；失败时 data_dict 为 None。
    """
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=date_str,
            end_date=date_str,
            adjust=adjust,
        )
    except Exception as e:
        return None, f"接口调用异常: {e}"

    if df is None or df.empty:
        return None, "未查询到该日期数据（可能非交易日或 symbol 有误）"

    row = df.iloc[0]
    cols = list(df.columns)

    data = {}
    data["列名"] = cols

    data["日期"] = str(row.get("日期", ""))

    for field in ["开盘", "最高", "最低", "收盘"]:
        if field in row.index:
            data[field] = float(row[field])
        else:
            data[field] = None

    if "涨跌幅" in row.index:
        data["涨跌幅"] = float(row["涨跌幅"])
    else:
        data["涨跌幅"] = None

    if "换手率" in row.index:
        data["换手率"] = float(row["换手率"])
    else:
        data["换手率"] = None

    if "成交额" in row.index:
        data["成交额"] = float(row["成交额"]) / 1e8
    elif "amount" in row.index:
        data["成交额"] = float(row["amount"]) / 1e8
    else:
        data["成交额"] = None

    return data, None


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

    # ============================================================
    # 日期保护：在任何联网请求之前拦截
    # ============================================================
    benchmark_date = THS_BENCHMARK["日期"]
    if args.date != benchmark_date:
        print(f"警告：当前基准数据对应日期为 {benchmark_date}，")
        print(f"但 --date 传入的是 {args.date}，对比结果无意义。")
        print(f"请更新 THS_BENCHMARK 后再运行，或使用 --date {benchmark_date}。")
        print()
        print("日期不匹配，未发起任何联网请求。")
        return

    # 导入 akshare
    try:
        import akshare as ak
    except ImportError:
        print("akshare 未安装。当前脚本不会自动安装依赖。请人工确认后再决定是否安装。")
        return

    date_str = args.date.replace("-", "")

    # ============================================================
    # 数据源检查区
    # ============================================================
    print("数据源检查：")

    # --- 主数据源：腾讯行情 ---
    tencent_data, tencent_err = fetch_tencent_data(ak, args.symbol, date_str, args.adjust)
    tencent_ok = tencent_data is not None
    if tencent_ok:
        print(f"  腾讯行情：成功")
    else:
        print(f"  腾讯行情：失败，失败原因：{tencent_err}")

    # --- Diagnostic 数据源：东方财富 ---
    eastmoney_data, eastmoney_err = fetch_eastmoney_data(
        ak, args.symbol, date_str, args.period, args.adjust
    )
    eastmoney_ok = eastmoney_data is not None
    if eastmoney_ok:
        print(f"  东方财富：成功")
    else:
        print(f"  东方财富：失败，失败原因：{eastmoney_err}")

    print()
    print("实际用于对比的数据源：腾讯行情")
    print()

    # ============================================================
    # 主流程：腾讯行情失败则直接结束
    # ============================================================
    if not tencent_ok:
        print("主数据源（腾讯行情）失败，无法进行对比。")
        print("东方财富仅为 diagnostic source，不替代主链。")
        print(f"失败原因：{tencent_err}")
        return

    # 腾讯日线未提供原始涨跌幅时，优先用收盘 / 昨收派生，避免 known-missing 字段导致主流程失败
    if tencent_data.get("涨跌幅") is None:
        derived_pct = _derive_pct_change(tencent_data.get("收盘"), THS_BENCHMARK.get("昨收"))
        if derived_pct is not None:
            tencent_data["涨跌幅"] = derived_pct
            tencent_data["涨跌幅来源"] = "由收盘/昨收计算"

    # ============================================================
    # 腾讯实时量比候选：仅做 diagnostic，不入主链
    # ============================================================
    realtime_volume_ratio = get_tencent_realtime_volume_ratio(args.symbol)
    print("腾讯实时 / quote 量比候选:")
    print(f"  状态: {realtime_volume_ratio['status']}")
    if realtime_volume_ratio["candidate_value"] is not None:
        print(f"  候选量比: {realtime_volume_ratio['candidate_value']:.2f}")
    else:
        print("  候选量比: 缺失")
    print(f"  主来源: {realtime_volume_ratio['primary_source'] or '无'}")
    print(f"  腾讯排行 lb: {realtime_volume_ratio['board_rank_lb']}" if realtime_volume_ratio["board_rank_lb"] is not None else "  腾讯排行 lb: 缺失")
    print(f"  qt index 49: {realtime_volume_ratio['qt_index_49_lb']}" if realtime_volume_ratio["qt_index_49_lb"] is not None else "  qt index 49: 缺失")
    if realtime_volume_ratio["board_rank_raw"] is not None:
        print(f"  腾讯排行原始片段: {realtime_volume_ratio['board_rank_raw']}")
    if realtime_volume_ratio["qt_raw_fragment"] is not None:
        print(f"  qt 原始片段: {realtime_volume_ratio['qt_raw_fragment']}")
    print(f"  提示: {realtime_volume_ratio['message']}")
    print()

    # 打印腾讯行情返回列名
    print(f"腾讯行情返回列名: {tencent_data['列名']}")
    print()

    # 打印腾讯行情数据
    print("腾讯行情查询结果:")
    print(f"  日期:    {tencent_data['日期']}")
    print(f"  开盘:    {tencent_data['开盘']}")
    print(f"  最高:    {tencent_data['最高']}")
    print(f"  最低:    {tencent_data['最低']}")
    print(f"  收盘:    {tencent_data['收盘']}")
    if tencent_data["涨跌幅"] is not None and tencent_data.get("涨跌幅来源") == "由收盘/昨收计算":
        print(f"  涨跌幅:  {tencent_data['涨跌幅']:.2f}（由收盘/昨收计算）")
    elif tencent_data["涨跌幅"] is not None:
        print(f"  涨跌幅:  {tencent_data['涨跌幅']:.2f}")
    else:
        print("  涨跌幅:  字段无法确认（腾讯日线接口通常不提供原始值）")
    print(f"  成交额:  {tencent_data['成交额']:.2f} 亿" if tencent_data['成交额'] is not None else "  成交额:  字段缺失")
    print(f"  换手率:  {tencent_data['换手率']}" if tencent_data['换手率'] is not None else "  换手率:  字段无法确认（腾讯日线接口通常不提供）")
    print()

    # ============================================================
    # 字段对比
    # ============================================================
    print("字段对比（数据源：腾讯行情）:")
    print("-" * 60)
    print(f"{'字段':<8} {'同花顺':>10} {'腾讯行情':>10} {'差异':>10} {'结果':>6}")
    print("-" * 60)

    fields = [
        ("开盘", THS_BENCHMARK["开盘"], tencent_data["开盘"], TOLERANCE["价格"], ""),
        ("最高", THS_BENCHMARK["最高"], tencent_data["最高"], TOLERANCE["价格"], ""),
        ("最低", THS_BENCHMARK["最低"], tencent_data["最低"], TOLERANCE["价格"], ""),
        ("收盘", THS_BENCHMARK["收盘"], tencent_data["收盘"], TOLERANCE["价格"], ""),
        ("涨跌幅", THS_BENCHMARK["涨跌幅"], tencent_data["涨跌幅"], TOLERANCE["涨跌幅"], ""),
        ("成交额", THS_BENCHMARK["成交额"], tencent_data["成交额"], TOLERANCE["成交额"], "亿"),
        ("换手率", THS_BENCHMARK["换手率"], tencent_data["换手率"], TOLERANCE["换手率"], ""),
    ]

    all_passed = True
    missing_fields = False

    for name, ths_val, src_val, tol, unit in fields:
        diff_str, passed = check_field(name, ths_val, src_val, tol, unit)

        if diff_str == "字段缺失":
            missing_fields = True
        if not passed:
            all_passed = False

        ths_str = f"{ths_val:.2f}" if ths_val is not None else "缺失"
        src_str = f"{src_val:.2f}" if src_val is not None else "缺失"
        result_str = "通过" if passed else "不通过"

        print(f"{name:<8} {ths_str:>10} {src_str:>10} {diff_str:>10} {result_str:>6}")

    print("-" * 60)
    print()

    # 输出结论
    if missing_fields:
        print("结论：腾讯行情字段不完整，需要继续校验。")
    elif all_passed:
        print("结论：腾讯行情与同花顺人工口径基本一致，可作为自动行情源候选。")
    else:
        print("结论：腾讯行情与同花顺存在差异，暂不自动替代人工口径。")

    print()
    print("注：量比不在对比中，因为腾讯日线接口通常不提供量比字段。")
    if "量比" in THS_BENCHMARK:
        benchmark_volume_ratio = THS_BENCHMARK["量比"]
        candidate_volume_ratio = realtime_volume_ratio["candidate_value"]
        if candidate_volume_ratio is None:
            print("注：腾讯实时量比候选缺失，仍需同花顺人工核对。")
        elif benchmark_volume_ratio is None:
            print("注：同花顺人工量比基准缺失，候选量比仅作 diagnostic，仍需同花顺人工核对。")
        elif abs(candidate_volume_ratio - benchmark_volume_ratio) <= 0.05:
            print("注：候选量比与人工核对一致。")
        else:
            print("注：候选量比与人工核对冲突，不入主链。")
    else:
        print("注：腾讯实时量比仅作候选字段，仍需同花顺人工核对。")


if __name__ == "__main__":
    main()
