"""服務層單元測試。"""

import unittest

from tw_stock_indicator.models.rules import IndicatorType, LogicOperator, Operator
from tw_stock_indicator.services import indicator_service, rule_service


class TestIndicatorService(unittest.TestCase):
    """指標服務測試。"""

    def test_get_demo_indicators_count(self):
        """確認回傳 8 筆示範指標。"""
        indicators = indicator_service.get_demo_indicators()
        self.assertEqual(len(indicators), 8)

    def test_get_demo_indicators_codes(self):
        """確認各指標代碼正確。"""
        indicators = indicator_service.get_demo_indicators()
        codes = [ind.code for ind in indicators]
        self.assertIn("win_rate", codes)
        self.assertIn("profit_factor", codes)
        self.assertIn("max_drawdown", codes)
        self.assertIn("sharpe_ratio", codes)

    def test_get_demo_indicators_values(self):
        """確認示範指標數值正確。"""
        indicators = indicator_service.get_demo_indicators()
        by_code = {ind.code: ind for ind in indicators}
        self.assertEqual(by_code["win_rate"].value, 62.5)
        self.assertEqual(by_code["total_trades"].value, 128)


class TestRuleService(unittest.TestCase):
    """規則服務測試。"""

    def setUp(self):
        """每個測試前清空儲存。"""
        rule_service.reset_store()

    def test_get_indicator_params(self):
        """確認取得指標參數。"""
        params = rule_service.get_indicator_params(IndicatorType.MA)
        self.assertIn("MA5", params)
        self.assertIn("MA20", params)

    def test_create_rule_group(self):
        """確認可建立規則群組。"""
        group = rule_service.create_rule_group("測試進場", "entry")
        self.assertEqual(group.name, "測試進場")
        self.assertEqual(group.rule_type, "entry")

    def test_add_condition(self):
        """確認可新增條件。"""
        group = rule_service.create_rule_group("測試", "entry")
        cond = rule_service.add_condition(
            group.id, IndicatorType.MA, "MA5", Operator.GT, "MA20",
        )
        self.assertIsNotNone(cond)
        self.assertEqual(len(group.conditions), 1)

    def test_add_condition_with_logic_operator(self):
        """確認第二個條件帶有邏輯運算子。"""
        group = rule_service.create_rule_group("測試", "entry")
        rule_service.add_condition(
            group.id, IndicatorType.MA, "MA5", Operator.GT, "MA20",
        )
        rule_service.add_condition(
            group.id, IndicatorType.RSI, "RSI12", Operator.LT, "70",
            LogicOperator.AND,
        )
        self.assertEqual(len(group.conditions), 2)
        self.assertEqual(len(group.logic_operators), 1)
        self.assertEqual(group.logic_operators[0], LogicOperator.AND)

    def test_add_condition_invalid_group(self):
        """確認對不存在的群組回傳 None。"""
        result = rule_service.add_condition(
            "invalid", IndicatorType.MA, "MA5", Operator.GT, "MA20",
        )
        self.assertIsNone(result)

    def test_remove_condition(self):
        """確認可移除條件。"""
        group = rule_service.create_rule_group("測試", "entry")
        cond = rule_service.add_condition(
            group.id, IndicatorType.MA, "MA5", Operator.GT, "MA20",
        )
        result = rule_service.remove_condition(group.id, cond.id)
        self.assertTrue(result)
        self.assertEqual(len(group.conditions), 0)

    def test_remove_condition_invalid(self):
        """確認移除不存在的條件回傳 False。"""
        group = rule_service.create_rule_group("測試", "entry")
        result = rule_service.remove_condition(group.id, "invalid")
        self.assertFalse(result)

    def test_get_all_rule_groups(self):
        """確認取得所有群組。"""
        rule_service.create_rule_group("進場", "entry")
        rule_service.create_rule_group("出場", "exit")
        groups = rule_service.get_all_rule_groups()
        self.assertEqual(len(groups), 2)

    def test_load_default_rules(self):
        """確認載入預設規則。"""
        rule_service.load_default_rules()
        groups = rule_service.get_all_rule_groups()
        self.assertEqual(len(groups), 2)
        types = {g.rule_type for g in groups}
        self.assertEqual(types, {"entry", "exit"})


if __name__ == "__main__":
    unittest.main()
