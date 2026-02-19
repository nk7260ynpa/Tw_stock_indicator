"""Flask 路由與 API 單元測試。"""

import json
import unittest
from unittest.mock import patch

from tw_stock_indicator.services import rule_service
from tw_stock_indicator.web import create_app


class TestWebBase(unittest.TestCase):
    """Web 測試基礎類別。"""

    def setUp(self):
        """建立測試用 Flask 應用程式。"""
        rule_service.reset_store()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()


class TestDashboard(TestWebBase):
    """儀表板路由測試。"""

    def test_index_status(self):
        """確認首頁回傳 200。"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_index_indicator_hidden(self):
        """確認績效指標區塊預設隱藏。"""
        resp = self.client.get("/")
        html = resp.data.decode("utf-8")
        self.assertIn('id="indicator-section"', html)
        self.assertIn('style="display:none;"', html)

    def test_index_contains_rule_designer(self):
        """確認首頁包含規則設計器。"""
        resp = self.client.get("/")
        html = resp.data.decode("utf-8")
        self.assertIn("rule-designer", html)

    def test_index_contains_stock_selector(self):
        """確認首頁包含股票選擇器。"""
        resp = self.client.get("/")
        html = resp.data.decode("utf-8")
        self.assertIn("stock-selector", html)
        self.assertIn("stock-search-input", html)


class TestIndicatorAPI(TestWebBase):
    """指標 API 測試。"""

    def test_get_params_ma(self):
        """確認取得 MA 參數。"""
        resp = self.client.get("/api/indicators/MA/params")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("MA5", data["params"])

    def test_get_params_invalid(self):
        """確認未知指標回傳 400。"""
        resp = self.client.get("/api/indicators/INVALID/params")
        self.assertEqual(resp.status_code, 400)


class TestRuleAPI(TestWebBase):
    """規則 API 測試。"""

    def test_list_rules(self):
        """確認可列出規則。"""
        resp = self.client.get("/api/rules")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIsInstance(data, list)
        # 預設載入兩組規則
        self.assertEqual(len(data), 2)

    def test_create_rule(self):
        """確認可建立規則群組。"""
        resp = self.client.post(
            "/api/rules",
            data=json.dumps({"name": "測試規則", "rule_type": "entry"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.data)
        self.assertEqual(data["name"], "測試規則")

    def test_create_rule_invalid(self):
        """確認缺少欄位回傳 400。"""
        resp = self.client.post(
            "/api/rules",
            data=json.dumps({"name": "test"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_add_and_delete_condition(self):
        """確認可新增與刪除條件。"""
        # 建立群組
        resp = self.client.post(
            "/api/rules",
            data=json.dumps({"name": "CRUD 測試", "rule_type": "entry"}),
            content_type="application/json",
        )
        group_id = json.loads(resp.data)["id"]

        # 新增條件
        resp = self.client.post(
            f"/api/rules/{group_id}/conditions",
            data=json.dumps({
                "indicator_type": "MA",
                "left_param": "MA5",
                "operator": ">",
                "right_param": "MA20",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        condition_id = json.loads(resp.data)["id"]

        # 刪除條件
        resp = self.client.delete(
            f"/api/rules/{group_id}/conditions/{condition_id}",
        )
        self.assertEqual(resp.status_code, 200)

    def test_add_condition_to_invalid_group(self):
        """確認對不存在群組新增條件回傳 404。"""
        resp = self.client.post(
            "/api/rules/invalid/conditions",
            data=json.dumps({
                "indicator_type": "MA",
                "left_param": "MA5",
                "operator": ">",
                "right_param": "MA20",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)


class TestStockSearchAPI(TestWebBase):
    """股票搜尋 API 測試。"""

    @patch("tw_stock_indicator.web.routes.api.stock_service")
    def test_search_stocks(self, mock_service):
        """確認搜尋回傳正確格式。"""
        mock_service.search_stocks.return_value = [
            {"code": "2330", "name": "台積電", "market": "TWSE"},
        ]

        resp = self.client.get("/api/stocks/search?q=2330")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "2330")

    def test_search_empty_keyword(self):
        """確認空關鍵字回傳空列表。"""
        resp = self.client.get("/api/stocks/search?q=")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data, [])

    @patch("tw_stock_indicator.web.routes.api.stock_service")
    def test_search_db_error(self, mock_service):
        """確認資料庫錯誤回傳 500。"""
        mock_service.search_stocks.side_effect = Exception("DB error")

        resp = self.client.get("/api/stocks/search?q=test")
        self.assertEqual(resp.status_code, 500)


class TestStockDailyAPI(TestWebBase):
    """股價日線 API 測試。"""

    @patch("tw_stock_indicator.web.routes.api.stock_service")
    def test_get_daily(self, mock_service):
        """確認取得日線資料。"""
        mock_service.get_stock_daily.return_value = [
            {"date": "2024-01-02", "open": 595.0, "high": 600.0,
             "low": 590.0, "close": 598.0, "volume": 25000},
        ]

        resp = self.client.get(
            "/api/stocks/TWSE/2330/daily?start=2024-01-01&end=2024-01-31"
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["close"], 598.0)

    def test_get_daily_invalid_market(self):
        """確認不支援的市場回傳 400。"""
        resp = self.client.get(
            "/api/stocks/INVALID/2330/daily?start=2024-01-01&end=2024-01-31"
        )
        self.assertEqual(resp.status_code, 400)

    def test_get_daily_missing_dates(self):
        """確認缺少日期參數回傳 400。"""
        resp = self.client.get("/api/stocks/TWSE/2330/daily")
        self.assertEqual(resp.status_code, 400)


class TestStockDateRangeAPI(TestWebBase):
    """股票日期範圍 API 測試。"""

    @patch("tw_stock_indicator.web.routes.api.stock_service")
    def test_get_date_range(self, mock_service):
        """確認取得日期範圍。"""
        mock_service.get_date_range.return_value = {
            "min_date": "2020-01-02",
            "max_date": "2024-12-31",
        }

        resp = self.client.get("/api/stocks/TWSE/2330/date-range")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["min_date"], "2020-01-02")
        self.assertEqual(data["max_date"], "2024-12-31")

    def test_get_date_range_invalid_market(self):
        """確認不支援的市場回傳 400。"""
        resp = self.client.get("/api/stocks/INVALID/2330/date-range")
        self.assertEqual(resp.status_code, 400)


class TestBacktestAPI(TestWebBase):
    """回測 API 測試。"""

    def test_backtest_success(self):
        """確認回測正確回傳指標。"""
        daily_data = [
            {"date": f"2024-01-{i+1:02d}", "open": 100.0 + i,
             "high": 102.0 + i, "low": 99.0 + i, "close": 101.0 + i,
             "volume": 1000}
            for i in range(30)
        ]

        resp = self.client.post(
            "/api/backtest",
            data=json.dumps({"daily_data": daily_data, "shares": 1000}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 8)

        codes = [d["code"] for d in data]
        self.assertIn("win_rate", codes)
        self.assertIn("total_trades", codes)

    def test_backtest_missing_data(self):
        """確認缺少 daily_data 回傳 400。"""
        resp = self.client.post(
            "/api/backtest",
            data=json.dumps({"shares": 1000}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_backtest_insufficient_data(self):
        """確認日線資料不足回傳 400。"""
        resp = self.client.post(
            "/api/backtest",
            data=json.dumps({
                "daily_data": [
                    {"date": "2024-01-01", "open": 100, "high": 101,
                     "low": 99, "close": 100, "volume": 1000}
                ],
                "shares": 1000,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_backtest_no_rules(self):
        """確認無規則時回傳 400。"""
        rule_service.reset_store()

        daily_data = [
            {"date": f"2024-01-{i+1:02d}", "open": 100.0 + i,
             "high": 102.0 + i, "low": 99.0 + i, "close": 101.0 + i,
             "volume": 1000}
            for i in range(10)
        ]

        resp = self.client.post(
            "/api/backtest",
            data=json.dumps({"daily_data": daily_data, "shares": 1000}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
