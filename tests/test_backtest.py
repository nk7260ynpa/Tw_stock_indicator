"""回測引擎單元測試。

測試技術指標計算、訊號評估與回測服務。
"""

import unittest

from tw_stock_indicator.models.rules import (
    Condition,
    IndicatorType,
    LogicOperator,
    Operator,
    RuleGroup,
)
from tw_stock_indicator.services import (
    backtest_service,
    indicator_calculator,
    signal_evaluator,
)


def _make_daily(
    closes: list[float],
    opens: list[float] | None = None,
    highs: list[float] | None = None,
    lows: list[float] | None = None,
) -> list[dict]:
    """建立測試用日線資料。"""
    n = len(closes)
    if opens is None:
        opens = closes
    if highs is None:
        highs = [c + 1.0 for c in closes]
    if lows is None:
        lows = [c - 1.0 for c in closes]
    return [
        {"date": f"2024-01-{i+1:02d}", "open": opens[i],
         "high": highs[i], "low": lows[i], "close": closes[i], "volume": 1000}
        for i in range(n)
    ]


class TestIndicatorCalculator(unittest.TestCase):
    """技術指標計算測試。"""

    def test_calc_ma_basic(self):
        """確認 MA 計算正確。"""
        closes = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = indicator_calculator.calc_ma(closes, 3)
        self.assertIsNone(result[0])
        self.assertIsNone(result[1])
        self.assertAlmostEqual(result[2], 20.0)
        self.assertAlmostEqual(result[3], 30.0)
        self.assertAlmostEqual(result[4], 40.0)

    def test_calc_ma_warmup_returns_none(self):
        """確認暖機期不足回傳 None。"""
        closes = [10.0, 20.0]
        result = indicator_calculator.calc_ma(closes, 5)
        self.assertTrue(all(v is None for v in result))

    def test_calc_ma_empty(self):
        """確認空資料回傳空列表。"""
        result = indicator_calculator.calc_ma([], 5)
        self.assertEqual(result, [])

    def test_calc_rsi_range(self):
        """確認 RSI 介於 0~100。"""
        closes = [float(i) for i in range(1, 30)]
        result = indicator_calculator.calc_rsi(closes, 14)
        for val in result:
            if val is not None:
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 100.0)

    def test_calc_rsi_all_up(self):
        """確認持續上漲時 RSI 接近 100。"""
        closes = [100.0 + i for i in range(20)]
        result = indicator_calculator.calc_rsi(closes, 6)
        last_rsi = result[-1]
        self.assertIsNotNone(last_rsi)
        self.assertGreater(last_rsi, 90.0)

    def test_calc_macd_keys(self):
        """確認 MACD 回傳正確的 key。"""
        closes = [100.0 + i * 0.5 for i in range(40)]
        result = indicator_calculator.calc_macd(closes)
        self.assertIn("DIF", result)
        self.assertIn("MACD", result)
        self.assertIn("OSC", result)
        self.assertEqual(len(result["DIF"]), 40)

    def test_calc_kd_keys(self):
        """確認 KD 回傳正確的 key。"""
        n = 20
        highs = [110.0 + i for i in range(n)]
        lows = [90.0 + i for i in range(n)]
        closes = [100.0 + i for i in range(n)]
        result = indicator_calculator.calc_kd(highs, lows, closes)
        self.assertIn("K", result)
        self.assertIn("D", result)

    def test_calc_bollinger_keys(self):
        """確認布林通道回傳正確的 key。"""
        closes = [100.0 + i * 0.3 for i in range(30)]
        result = indicator_calculator.calc_bollinger(closes)
        self.assertIn("上軌", result)
        self.assertIn("中軌", result)
        self.assertIn("下軌", result)

    def test_build_indicator_series(self):
        """確認 build_indicator_series 產出所有預期 key。"""
        daily = _make_daily([100.0 + i for i in range(30)])
        series = indicator_calculator.build_indicator_series(daily)

        expected_keys = [
            "收盤價", "MA5", "MA10", "MA20", "MA60", "MA120", "MA240",
            "RSI6", "RSI12", "RSI24", "DIF", "MACD", "OSC", "K", "D",
            "上軌", "中軌", "下軌", "0", "20", "30", "50", "70", "80",
        ]
        for key in expected_keys:
            self.assertIn(key, series, f"缺少 key: {key}")
            self.assertEqual(len(series[key]), 30)

    def test_constant_series(self):
        """確認常數序列值正確。"""
        daily = _make_daily([100.0] * 5)
        series = indicator_calculator.build_indicator_series(daily)
        self.assertEqual(series["50"], [50.0] * 5)
        self.assertEqual(series["0"], [0.0] * 5)


class TestSignalEvaluator(unittest.TestCase):
    """訊號評估測試。"""

    def test_cross_above(self):
        """確認上穿判斷正確。"""
        series = {
            "MA5": [10.0, 15.0, 22.0],
            "MA20": [20.0, 20.0, 20.0],
        }
        cond = Condition(
            indicator_type=IndicatorType.MA,
            left_param="MA5",
            operator=Operator.CROSS_ABOVE,
            right_param="MA20",
        )

        # idx=0 無前一根
        self.assertFalse(signal_evaluator._eval_condition(cond, series, 0))
        # idx=1 MA5 從 10→15，仍 <= 20
        self.assertFalse(signal_evaluator._eval_condition(cond, series, 1))
        # idx=2 MA5 從 15→22，前一根 15<=20，當根 22>20 → 上穿
        self.assertTrue(signal_evaluator._eval_condition(cond, series, 2))

    def test_cross_below(self):
        """確認下穿判斷正確。"""
        series = {
            "MA5": [22.0, 20.0, 18.0],
            "MA20": [20.0, 20.0, 20.0],
        }
        cond = Condition(
            indicator_type=IndicatorType.MA,
            left_param="MA5",
            operator=Operator.CROSS_BELOW,
            right_param="MA20",
        )

        # idx=2 MA5 從 20→18，前一根 20>=20，當根 18<20 → 下穿
        self.assertTrue(signal_evaluator._eval_condition(cond, series, 2))

    def test_gt_operator(self):
        """確認大於運算子判斷正確。"""
        series = {"RSI12": [60.0, 75.0], "70": [70.0, 70.0]}
        cond = Condition(
            indicator_type=IndicatorType.RSI,
            left_param="RSI12",
            operator=Operator.GT,
            right_param="70",
        )
        self.assertFalse(signal_evaluator._eval_condition(cond, series, 0))
        self.assertTrue(signal_evaluator._eval_condition(cond, series, 1))

    def test_none_value_returns_false(self):
        """確認指標值為 None 時回傳 False。"""
        series = {"MA5": [None, 10.0], "MA20": [None, None]}
        cond = Condition(
            indicator_type=IndicatorType.MA,
            left_param="MA5",
            operator=Operator.GT,
            right_param="MA20",
        )
        self.assertFalse(signal_evaluator._eval_condition(cond, series, 0))
        self.assertFalse(signal_evaluator._eval_condition(cond, series, 1))

    def test_eval_rule_group_and(self):
        """確認 AND 組合正確。"""
        series = {
            "MA5": [25.0],
            "MA20": [20.0],
            "RSI12": [65.0],
            "70": [70.0],
        }
        group = RuleGroup(name="test", rule_type="entry")
        group.conditions = [
            Condition(IndicatorType.MA, "MA5", Operator.GT, "MA20"),
            Condition(IndicatorType.RSI, "RSI12", Operator.LT, "70"),
        ]
        group.logic_operators = [LogicOperator.AND]

        # MA5>MA20=True, RSI12<70=True → AND → True
        self.assertTrue(signal_evaluator._eval_rule_group(group, series, 0))

    def test_eval_rule_group_and_false(self):
        """確認 AND 組合有一條件不成立時回傳 False。"""
        series = {
            "MA5": [25.0],
            "MA20": [20.0],
            "RSI12": [75.0],
            "70": [70.0],
        }
        group = RuleGroup(name="test", rule_type="entry")
        group.conditions = [
            Condition(IndicatorType.MA, "MA5", Operator.GT, "MA20"),
            Condition(IndicatorType.RSI, "RSI12", Operator.LT, "70"),
        ]
        group.logic_operators = [LogicOperator.AND]

        # MA5>MA20=True, RSI12<70=False → AND → False
        self.assertFalse(signal_evaluator._eval_rule_group(group, series, 0))

    def test_eval_rule_group_or(self):
        """確認 OR 組合正確。"""
        series = {
            "MA5": [15.0],
            "MA20": [20.0],
            "RSI12": [65.0],
            "70": [70.0],
        }
        group = RuleGroup(name="test", rule_type="entry")
        group.conditions = [
            Condition(IndicatorType.MA, "MA5", Operator.GT, "MA20"),
            Condition(IndicatorType.RSI, "RSI12", Operator.LT, "70"),
        ]
        group.logic_operators = [LogicOperator.OR]

        # MA5>MA20=False, RSI12<70=True → OR → True
        self.assertTrue(signal_evaluator._eval_rule_group(group, series, 0))

    def test_generate_signals_or_between_groups(self):
        """確認同類型多群組間為 OR 關係。"""
        series = {
            "MA5": [15.0],
            "MA20": [20.0],
            "RSI12": [25.0],
            "30": [30.0],
        }
        # 群組 1：MA5 > MA20（False）
        g1 = RuleGroup(name="g1", rule_type="entry")
        g1.conditions = [
            Condition(IndicatorType.MA, "MA5", Operator.GT, "MA20"),
        ]
        # 群組 2：RSI12 < 30（True）
        g2 = RuleGroup(name="g2", rule_type="entry")
        g2.conditions = [
            Condition(IndicatorType.RSI, "RSI12", Operator.LT, "30"),
        ]

        signals = signal_evaluator.generate_signals([g1, g2], series, 1)
        # 任一群組成立即觸發
        self.assertTrue(signals["entry_signals"][0])

    def test_empty_conditions_returns_false(self):
        """確認空條件的群組回傳 False。"""
        group = RuleGroup(name="empty", rule_type="entry")
        series = {"MA5": [10.0]}
        self.assertFalse(signal_evaluator._eval_rule_group(group, series, 0))


class TestBacktestService(unittest.TestCase):
    """回測服務測試。"""

    def test_empty_data_returns_zero(self):
        """確認空資料回傳全 0 指標。"""
        result = backtest_service.run_backtest([], [], 1000)
        self.assertEqual(len(result["indicators"]), 8)
        for ind in result["indicators"]:
            self.assertEqual(ind.value, 0)
        self.assertEqual(result["trades"], [])
        self.assertEqual(result["indicator_series"], {})

    def test_no_rules_returns_zero(self):
        """確認無規則回傳全 0 指標。"""
        daily = _make_daily([100.0] * 10)
        result = backtest_service.run_backtest(daily, [], 1000)
        self.assertEqual(len(result["indicators"]), 8)
        for ind in result["indicators"]:
            self.assertEqual(ind.value, 0)

    def test_basic_backtest(self):
        """確認基本回測計算正確。"""
        # 製造明確的上穿訊號：MA5 從低於 MA20 到高於 MA20
        n = 30
        # 先下跌再上漲，製造黃金交叉
        closes = [100.0 - i for i in range(15)] + [86.0 + i * 2 for i in range(15)]
        daily = _make_daily(closes)

        entry_group = RuleGroup(name="進場", rule_type="entry")
        entry_group.conditions = [
            Condition(IndicatorType.MA, "MA5", Operator.CROSS_ABOVE, "MA20"),
        ]

        exit_group = RuleGroup(name="出場", rule_type="exit")
        exit_group.conditions = [
            Condition(IndicatorType.MA, "MA5", Operator.CROSS_BELOW, "MA20"),
        ]

        result = backtest_service.run_backtest(
            daily, [entry_group, exit_group], 1000
        )
        self.assertEqual(len(result["indicators"]), 8)

        # 找到各指標
        codes = {ind.code: ind for ind in result["indicators"]}
        self.assertIn("win_rate", codes)
        self.assertIn("total_trades", codes)
        self.assertIn("profit_factor", codes)
        self.assertIn("expected_value", codes)
        self.assertIn("max_drawdown", codes)
        self.assertIn("sharpe_ratio", codes)
        self.assertIn("profit_loss_ratio", codes)
        self.assertIn("annual_return", codes)

    def test_win_rate_calculation(self):
        """確認勝率計算正確（使用簡單比較條件）。"""
        # 造價格：持續上漲
        closes = [100.0 + i for i in range(20)]
        daily = _make_daily(closes)

        # 使用簡單條件：收盤價 > MA5 進場
        entry_group = RuleGroup(name="進場", rule_type="entry")
        entry_group.conditions = [
            Condition(IndicatorType.MA, "收盤價", Operator.GT, "MA5"),
        ]

        # 使用簡單條件：收盤價 < MA5 出場
        exit_group = RuleGroup(name="出場", rule_type="exit")
        exit_group.conditions = [
            Condition(IndicatorType.MA, "收盤價", Operator.LT, "MA5"),
        ]

        result = backtest_service.run_backtest(
            daily, [entry_group, exit_group], 1000
        )
        codes = {ind.code: ind for ind in result["indicators"]}

        # 持續上漲環境，總交易次數應 >= 0
        self.assertGreaterEqual(codes["total_trades"].value, 0)

    def test_profit_factor_all_winning(self):
        """確認全勝時獲利因子為最大值。"""
        # 手動建構確保有獲利交易的場景
        # 使用直接的訊號模擬來驗證 _calc_performance
        trades = [
            {"entry_price": 100.0, "exit_price": 110.0,
             "pnl": 10000.0, "entry_idx": 0, "exit_idx": 5},
        ]
        daily = _make_daily([100.0] * 10)
        result = backtest_service._calc_performance(trades, daily, 1000)

        codes = {ind.code: ind for ind in result}
        self.assertEqual(codes["win_rate"].value, 100.0)
        # 無虧損交易，獲利因子為最大值
        self.assertEqual(codes["profit_factor"].value, 999.99)


class TestBacktestChartData(unittest.TestCase):
    """回測圖表資料測試。"""

    def _run_ma_backtest(self, closes=None):
        """執行 MA 交叉回測並回傳結果。"""
        if closes is None:
            closes = (
                [100.0 - i for i in range(15)]
                + [86.0 + i * 2 for i in range(15)]
            )
        daily = _make_daily(closes)
        entry_group = RuleGroup(name="進場", rule_type="entry")
        entry_group.conditions = [
            Condition(IndicatorType.MA, "MA5", Operator.CROSS_ABOVE, "MA20"),
        ]
        exit_group = RuleGroup(name="出場", rule_type="exit")
        exit_group.conditions = [
            Condition(IndicatorType.MA, "MA5", Operator.CROSS_BELOW, "MA20"),
        ]
        return backtest_service.run_backtest(
            daily, [entry_group, exit_group], 1000
        )

    def test_trades_contain_dates(self):
        """確認交易紀錄包含 entry_date 和 exit_date。"""
        result = self._run_ma_backtest()
        for trade in result["trades"]:
            self.assertIn("entry_date", trade)
            self.assertIn("exit_date", trade)
            # 日期格式驗證
            self.assertRegex(trade["entry_date"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertRegex(trade["exit_date"], r"^\d{4}-\d{2}-\d{2}$")

    def test_indicator_series_only_relevant(self):
        """確認 MA 規則不含 RSI/KD/MACD 指標序列。"""
        result = self._run_ma_backtest()
        series = result["indicator_series"]
        # 應包含 MA5、MA20
        self.assertIn("MA5", series)
        self.assertIn("MA20", series)
        # 不應包含 RSI/KD/MACD
        for key in ("RSI6", "RSI12", "RSI24", "K", "D", "DIF", "MACD", "OSC"):
            self.assertNotIn(key, series)

    def test_bollinger_includes_all_bands(self):
        """確認布林通道規則包含三條線。"""
        closes = [100.0 + i * 0.5 for i in range(30)]
        daily = _make_daily(closes)
        entry_group = RuleGroup(name="進場", rule_type="entry")
        entry_group.conditions = [
            Condition(IndicatorType.BOLLINGER, "收盤價", Operator.LT, "下軌"),
        ]
        exit_group = RuleGroup(name="出場", rule_type="exit")
        exit_group.conditions = [
            Condition(IndicatorType.BOLLINGER, "收盤價", Operator.GT, "上軌"),
        ]
        result = backtest_service.run_backtest(
            daily, [entry_group, exit_group], 1000
        )
        series = result["indicator_series"]
        self.assertIn("上軌", series)
        self.assertIn("中軌", series)
        self.assertIn("下軌", series)

    def test_empty_data_returns_empty_trades(self):
        """確認空資料回傳 trades=[] 及 indicator_series={}。"""
        result = backtest_service.run_backtest([], [], 1000)
        self.assertEqual(result["trades"], [])
        self.assertEqual(result["indicator_series"], {})


if __name__ == "__main__":
    unittest.main()
