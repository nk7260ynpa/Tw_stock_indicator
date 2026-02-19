"""資料模型單元測試。"""

import unittest

from tw_stock_indicator.models.indicators import Indicator
from tw_stock_indicator.models.rules import (
    Condition,
    IndicatorType,
    LogicOperator,
    Operator,
    RuleGroup,
)


class TestIndicator(unittest.TestCase):
    """Indicator dataclass 測試。"""

    def test_create_indicator(self):
        """確認可正常建立 Indicator。"""
        ind = Indicator(
            code="win_rate", name="勝率", value=62.5,
            unit="%", description="勝率說明",
        )
        self.assertEqual(ind.code, "win_rate")
        self.assertEqual(ind.name, "勝率")
        self.assertEqual(ind.value, 62.5)

    def test_formatted_value_percent(self):
        """確認百分比格式化。"""
        ind = Indicator(
            code="win_rate", name="勝率", value=62.5,
            unit="%", description="",
        )
        self.assertEqual(ind.formatted_value(), "62.5%")

    def test_formatted_value_times(self):
        """確認倍數格式化。"""
        ind = Indicator(
            code="pf", name="獲利因子", value=1.85,
            unit="倍", description="",
        )
        self.assertEqual(ind.formatted_value(), "1.85 倍")

    def test_formatted_value_currency(self):
        """確認元格式化。"""
        ind = Indicator(
            code="ev", name="期望值", value=1250,
            unit="元", description="",
        )
        self.assertEqual(ind.formatted_value(), "1,250 元")

    def test_formatted_value_count(self):
        """確認次數格式化。"""
        ind = Indicator(
            code="trades", name="總交易次數", value=128,
            unit="次", description="",
        )
        self.assertEqual(ind.formatted_value(), "128 次")

    def test_frozen(self):
        """確認 Indicator 為不可變物件。"""
        ind = Indicator(
            code="test", name="測試", value=1.0,
            unit="%", description="",
        )
        with self.assertRaises(AttributeError):
            ind.value = 2.0


class TestRuleModels(unittest.TestCase):
    """規則資料模型測試。"""

    def test_indicator_type_enum(self):
        """確認 IndicatorType 列舉值。"""
        self.assertEqual(IndicatorType.MA.value, "MA")
        self.assertEqual(IndicatorType.RSI.value, "RSI")

    def test_operator_enum(self):
        """確認 Operator 列舉值。"""
        self.assertEqual(Operator.GT.value, ">")
        self.assertEqual(Operator.CROSS_ABOVE.value, "上穿")

    def test_create_condition(self):
        """確認可建立 Condition。"""
        cond = Condition(
            indicator_type=IndicatorType.MA,
            left_param="MA5",
            operator=Operator.CROSS_ABOVE,
            right_param="MA20",
        )
        self.assertEqual(cond.indicator_type, IndicatorType.MA)
        self.assertEqual(cond.left_param, "MA5")
        self.assertIsNotNone(cond.id)

    def test_create_rule_group(self):
        """確認可建立 RuleGroup。"""
        group = RuleGroup(name="測試規則", rule_type="entry")
        self.assertEqual(group.name, "測試規則")
        self.assertEqual(group.rule_type, "entry")
        self.assertEqual(len(group.conditions), 0)

    def test_rule_group_with_conditions(self):
        """確認 RuleGroup 可包含條件。"""
        cond = Condition(
            indicator_type=IndicatorType.RSI,
            left_param="RSI12",
            operator=Operator.LT,
            right_param="70",
        )
        group = RuleGroup(
            name="測試", rule_type="entry",
            conditions=[cond],
            logic_operators=[],
        )
        self.assertEqual(len(group.conditions), 1)


if __name__ == "__main__":
    unittest.main()
