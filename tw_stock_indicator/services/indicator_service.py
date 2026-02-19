"""指標服務模組。

提供靜態示範指標資料。
"""

from tw_stock_indicator.models.indicators import Indicator


def get_demo_indicators() -> list[Indicator]:
    """回傳 8 項靜態示範指標。

    Returns:
        包含 8 個 Indicator 物件的列表。
    """
    return [
        Indicator(
            code="win_rate",
            name="勝率",
            value=62.5,
            unit="%",
            description="獲利交易佔總交易次數的比例",
        ),
        Indicator(
            code="profit_factor",
            name="獲利因子",
            value=1.85,
            unit="倍",
            description="總獲利金額除以總虧損金額",
        ),
        Indicator(
            code="expected_value",
            name="期望值",
            value=1250,
            unit="元",
            description="每筆交易的平均預期損益",
        ),
        Indicator(
            code="max_drawdown",
            name="最大回撤",
            value=-15.3,
            unit="%",
            description="從資產高點到低點的最大跌幅",
        ),
        Indicator(
            code="sharpe_ratio",
            name="夏普比率",
            value=1.42,
            unit="倍",
            description="每承受一單位風險所獲得的超額報酬",
        ),
        Indicator(
            code="profit_loss_ratio",
            name="平均獲利虧損比",
            value=2.1,
            unit="倍",
            description="平均獲利金額除以平均虧損金額",
        ),
        Indicator(
            code="annual_return",
            name="年化報酬率",
            value=18.7,
            unit="%",
            description="投資報酬換算為年度的複利報酬率",
        ),
        Indicator(
            code="total_trades",
            name="總交易次數",
            value=128,
            unit="次",
            description="回測期間的總交易筆數",
        ),
    ]
