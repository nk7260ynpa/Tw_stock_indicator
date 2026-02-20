"""回測服務模組。

協調技術指標計算、訊號評估與交易模擬，產出績效指標。
"""

import logging
import math

from tw_stock_indicator.models.indicators import Indicator
from tw_stock_indicator.models.rules import RuleGroup
from tw_stock_indicator.services import indicator_calculator, signal_evaluator

logger = logging.getLogger(__name__)

# 無風險年利率（台灣定存利率約 1.5%）
_RISK_FREE_RATE = 0.015
# 一年約 250 個交易日
_TRADING_DAYS_PER_YEAR = 250


def _zero_indicators() -> list[Indicator]:
    """回傳全 0 的績效指標。"""
    return [
        Indicator("win_rate", "勝率", 0.0, "%", "獲利交易佔總交易次數的比例"),
        Indicator("profit_factor", "獲利因子", 0.0, "倍", "總獲利金額除以總虧損金額"),
        Indicator("expected_value", "期望值", 0.0, "元", "每筆交易的平均預期損益"),
        Indicator("max_drawdown", "最大回撤", 0.0, "%", "從資產高點到低點的最大跌幅"),
        Indicator("sharpe_ratio", "夏普比率", 0.0, "倍", "每承受一單位風險所獲得的超額報酬"),
        Indicator("profit_loss_ratio", "平均獲利虧損比", 0.0, "倍",
                  "平均獲利金額除以平均虧損金額"),
        Indicator("annual_return", "年化報酬率", 0.0, "%",
                  "投資報酬換算為年度的複利報酬率"),
        Indicator("total_trades", "總交易次數", 0, "次", "回測期間的總交易筆數"),
    ]


def _simulate_trades(
    daily_data: list[dict],
    entry_signals: list[bool],
    exit_signals: list[bool],
    shares: int,
) -> list[dict]:
    """模擬交易。

    隔日開盤成交，同時只持有一個部位。
    最後一根 K 棒若仍持倉，以收盤價強制出場。

    Args:
        daily_data: 日線資料。
        entry_signals: 進場訊號。
        exit_signals: 出場訊號。
        shares: 每筆交易股數。

    Returns:
        交易紀錄列表，每筆包含 entry_price、exit_price、pnl、
        entry_idx、exit_idx、entry_date、exit_date。
    """
    n = len(daily_data)
    trades: list[dict] = []
    in_position = False
    entry_price = 0.0
    entry_idx = 0

    for i in range(n - 1):
        if not in_position and entry_signals[i]:
            # 訊號日 i → 次日 i+1 開盤買入
            entry_price = daily_data[i + 1]["open"]
            entry_idx = i + 1
            in_position = True
        elif in_position and exit_signals[i]:
            # 訊號日 i → 次日 i+1 開盤賣出
            exit_idx = i + 1
            exit_price = daily_data[exit_idx]["open"]
            pnl = (exit_price - entry_price) * shares
            trades.append({
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl": pnl,
                "entry_idx": entry_idx,
                "exit_idx": exit_idx,
                "entry_date": daily_data[entry_idx]["date"],
                "exit_date": daily_data[exit_idx]["date"],
            })
            in_position = False

    # 最後仍持倉：以最後一根收盤價強制出場
    if in_position:
        exit_price = daily_data[-1]["close"]
        pnl = (exit_price - entry_price) * shares
        trades.append({
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "entry_idx": entry_idx,
            "exit_idx": n - 1,
            "entry_date": daily_data[entry_idx]["date"],
            "exit_date": daily_data[n - 1]["date"],
        })

    return trades


def _calc_performance(
    trades: list[dict],
    daily_data: list[dict],
    shares: int,
) -> list[Indicator]:
    """根據交易紀錄計算 8 項績效指標。

    Args:
        trades: 交易紀錄列表。
        daily_data: 日線資料。
        shares: 每筆交易股數。

    Returns:
        包含 8 個 Indicator 的列表。
    """
    total_trades = len(trades)
    if total_trades == 0:
        return _zero_indicators()

    # 基礎統計
    winning = [t for t in trades if t["pnl"] > 0]
    losing = [t for t in trades if t["pnl"] < 0]

    total_profit = sum(t["pnl"] for t in winning)
    total_loss = sum(t["pnl"] for t in losing)

    # 勝率
    win_rate = len(winning) / total_trades * 100

    # 獲利因子
    profit_factor = (
        total_profit / abs(total_loss) if total_loss != 0 else float("inf")
    )
    if profit_factor == float("inf"):
        profit_factor = 999.99

    # 期望值
    total_pnl = sum(t["pnl"] for t in trades)
    expected_value = total_pnl / total_trades

    # 獲利虧損比
    avg_profit = total_profit / len(winning) if winning else 0.0
    avg_loss = abs(total_loss) / len(losing) if losing else 0.0
    profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 999.99

    # 最大回撤（基於資產曲線）
    # 以第一筆交易的買入成本作為初始資本
    initial_capital = trades[0]["entry_price"] * shares
    equity = initial_capital
    peak = equity
    max_dd = 0.0

    for trade in trades:
        equity += trade["pnl"]
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak * 100 if peak > 0 else 0.0
        if drawdown > max_dd:
            max_dd = drawdown

    max_drawdown = -round(max_dd, 2)

    # 年化報酬率
    n_days = len(daily_data)
    years = n_days / _TRADING_DAYS_PER_YEAR if n_days > 0 else 1.0
    final_equity = initial_capital + total_pnl
    if initial_capital > 0 and final_equity > 0 and years > 0:
        annual_return = ((final_equity / initial_capital) ** (1.0 / years) - 1) * 100
    elif initial_capital > 0 and years > 0:
        annual_return = -100.0
    else:
        annual_return = 0.0

    # 夏普比率（以每筆交易報酬率計算）
    trade_returns = []
    for t in trades:
        cost = t["entry_price"] * shares
        if cost > 0:
            trade_returns.append(t["pnl"] / cost)

    if len(trade_returns) >= 2:
        avg_return = sum(trade_returns) / len(trade_returns)
        variance = sum((r - avg_return) ** 2 for r in trade_returns) / (
            len(trade_returns) - 1
        )
        std_return = math.sqrt(variance) if variance > 0 else 0.0
        # 年化
        trades_per_year = _TRADING_DAYS_PER_YEAR / max(
            n_days / total_trades, 1
        )
        annualized_return = avg_return * trades_per_year
        annualized_std = std_return * math.sqrt(trades_per_year)
        sharpe = (
            (annualized_return - _RISK_FREE_RATE) / annualized_std
            if annualized_std > 0
            else 0.0
        )
    else:
        sharpe = 0.0

    return [
        Indicator("win_rate", "勝率", round(win_rate, 1), "%",
                  "獲利交易佔總交易次數的比例"),
        Indicator("profit_factor", "獲利因子", round(profit_factor, 2), "倍",
                  "總獲利金額除以總虧損金額"),
        Indicator("expected_value", "期望值", round(expected_value, 2), "元",
                  "每筆交易的平均預期損益"),
        Indicator("max_drawdown", "最大回撤", max_drawdown, "%",
                  "從資產高點到低點的最大跌幅"),
        Indicator("sharpe_ratio", "夏普比率", round(sharpe, 2), "倍",
                  "每承受一單位風險所獲得的超額報酬"),
        Indicator("profit_loss_ratio", "平均獲利虧損比",
                  round(profit_loss_ratio, 2), "倍",
                  "平均獲利金額除以平均虧損金額"),
        Indicator("annual_return", "年化報酬率", round(annual_return, 2), "%",
                  "投資報酬換算為年度的複利報酬率"),
        Indicator("total_trades", "總交易次數", total_trades, "次",
                  "回測期間的總交易筆數"),
    ]


def _extract_relevant_series(
    rule_groups: list[RuleGroup],
    series: dict[str, list[float | None]],
) -> dict[str, list[float | None]]:
    """根據規則群組中引用的參數，篩選出需要的技術指標序列。

    布林通道自動包含三條線、MACD 包含 DIF/MACD/OSC、KD 包含 K/D。
    排除常數（0, 20, 30, 50, 70, 80）和收盤價（前端已有）。

    Args:
        rule_groups: 規則群組列表。
        series: 完整的技術指標序列字典。

    Returns:
        篩選後的指標序列字典。
    """
    excluded = {"0", "20", "30", "50", "70", "80", "收盤價"}

    # 收集規則中引用的所有參數
    referenced: set[str] = set()
    for group in rule_groups:
        for cond in group.conditions:
            referenced.add(cond.left_param)
            referenced.add(cond.right_param)

    # 擴展關聯指標
    expanded: set[str] = set()
    for param in referenced:
        if param in excluded:
            continue
        expanded.add(param)
        # 布林通道：任一軌被引用，三條都包含
        if param in ("上軌", "中軌", "下軌"):
            expanded.update(("上軌", "中軌", "下軌"))
        # MACD：任一被引用，三個都包含
        if param in ("DIF", "MACD", "OSC"):
            expanded.update(("DIF", "MACD", "OSC"))
        # KD：任一被引用，兩個都包含
        if param in ("K", "D"):
            expanded.update(("K", "D"))

    result: dict[str, list[float | None]] = {}
    for key in expanded:
        if key in series:
            result[key] = series[key]

    return result


def run_backtest(
    daily_data: list[dict],
    rule_groups: list[RuleGroup],
    shares: int = 1000,
) -> dict:
    """執行回測。

    流程：
    1. 計算所有技術指標
    2. 產出進出場訊號
    3. 模擬交易
    4. 計算績效指標

    Args:
        daily_data: 日線資料列表。
        rule_groups: 規則群組列表。
        shares: 每筆交易股數。

    Returns:
        包含 indicators（績效指標列表）、trades（交易紀錄）、
        indicator_series（相關技術指標序列）的字典。
    """
    empty_result = {
        "indicators": _zero_indicators(),
        "trades": [],
        "indicator_series": {},
    }

    if not daily_data or len(daily_data) < 2:
        logger.warning("日線資料不足，無法執行回測")
        return empty_result

    if not rule_groups:
        logger.warning("無規則群組，無法執行回測")
        return empty_result

    # 1. 計算技術指標
    series = indicator_calculator.build_indicator_series(daily_data)
    n = len(daily_data)

    # 2. 產出訊號
    signals = signal_evaluator.generate_signals(rule_groups, series, n)

    # 3. 模擬交易
    trades = _simulate_trades(
        daily_data, signals["entry_signals"], signals["exit_signals"], shares
    )

    logger.info("回測完成：%d 筆交易", len(trades))

    # 4. 計算績效
    indicators = _calc_performance(trades, daily_data, shares)

    # 5. 篩選相關指標序列
    indicator_series = _extract_relevant_series(rule_groups, series)

    return {
        "indicators": indicators,
        "trades": trades,
        "indicator_series": indicator_series,
    }
