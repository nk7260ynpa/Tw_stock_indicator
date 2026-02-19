"""股票資料查詢服務單元測試。"""

import unittest
from unittest.mock import MagicMock, patch

from tw_stock_indicator.services import stock_service


class TestGetDbEngine(unittest.TestCase):
    """get_db_engine 測試。"""

    def setUp(self):
        """每個測試前重設 engine。"""
        stock_service.reset_engine()

    def tearDown(self):
        """每個測試後重設 engine。"""
        stock_service.reset_engine()

    @patch("tw_stock_indicator.services.stock_service.create_engine")
    @patch.dict("os.environ", {
        "DB_HOST": "testhost",
        "DB_USER": "testuser",
        "DB_PASSWORD": "testpass",
        "DB_PORT": "3307",
    })
    def test_engine_created_with_env_vars(self, mock_create):
        """確認從環境變數建立 engine。"""
        mock_engine = MagicMock()
        mock_create.return_value = mock_engine

        engine = stock_service.get_db_engine()

        mock_create.assert_called_once_with(
            "mysql+pymysql://testuser:testpass@testhost:3307/",
            pool_pre_ping=True,
        )
        self.assertEqual(engine, mock_engine)

    @patch("tw_stock_indicator.services.stock_service.create_engine")
    def test_engine_cached(self, mock_create):
        """確認 engine 只建立一次。"""
        mock_create.return_value = MagicMock()

        stock_service.get_db_engine()
        stock_service.get_db_engine()

        mock_create.assert_called_once()


class TestSearchStocks(unittest.TestCase):
    """search_stocks 測試。"""

    def setUp(self):
        """重設 engine。"""
        stock_service.reset_engine()

    def tearDown(self):
        """重設 engine。"""
        stock_service.reset_engine()

    @patch("tw_stock_indicator.services.stock_service.get_db_engine")
    def test_search_returns_formatted_results(self, mock_get_engine):
        """確認搜尋結果格式正確。"""
        # 模擬 TWSE 結果
        twse_row = {"code": "2330  ", "name": "台積電  "}
        # 模擬 TPEX 結果
        tpex_row = {"code": "6510  ", "name": "精測  "}

        mock_conn = MagicMock()
        # 第一次 execute 回傳 TWSE 結果，第二次回傳 TPEX 結果
        twse_result = MagicMock()
        twse_result.mappings.return_value = [twse_row]
        tpex_result = MagicMock()
        tpex_result.mappings.return_value = [tpex_row]
        mock_conn.execute.side_effect = [twse_result, tpex_result]

        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_engine.connect.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_get_engine.return_value = mock_engine

        results = stock_service.search_stocks("2330")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["code"], "2330")
        self.assertEqual(results[0]["name"], "台積電")
        self.assertEqual(results[0]["market"], "TWSE")
        self.assertEqual(results[1]["market"], "TPEX")

    @patch("tw_stock_indicator.services.stock_service.get_db_engine")
    def test_search_empty_results(self, mock_get_engine):
        """確認無結果時回傳空列表。"""
        mock_conn = MagicMock()
        empty_result = MagicMock()
        empty_result.mappings.return_value = []
        mock_conn.execute.side_effect = [empty_result, empty_result]

        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_engine.connect.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_get_engine.return_value = mock_engine

        results = stock_service.search_stocks("不存在")
        self.assertEqual(results, [])


class TestGetStockDaily(unittest.TestCase):
    """get_stock_daily 測試。"""

    def setUp(self):
        """重設 engine。"""
        stock_service.reset_engine()

    def tearDown(self):
        """重設 engine。"""
        stock_service.reset_engine()

    @patch("tw_stock_indicator.services.stock_service.get_db_engine")
    def test_twse_daily_returns_unified_format(self, mock_get_engine):
        """確認 TWSE 日線資料回傳統一格式。"""
        row = {
            "date": "2024-01-02",
            "open": 595.0,
            "high": 600.0,
            "low": 590.0,
            "close": 598.0,
            "volume": 25000,
        }

        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value = [row]
        mock_conn.execute.return_value = mock_result

        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_engine.connect.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_get_engine.return_value = mock_engine

        results = stock_service.get_stock_daily(
            "TWSE", "2330", "2024-01-01", "2024-01-31"
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["date"], "2024-01-02")
        self.assertEqual(results[0]["open"], 595.0)
        self.assertEqual(results[0]["close"], 598.0)
        self.assertEqual(results[0]["volume"], 25000)

    @patch("tw_stock_indicator.services.stock_service.get_db_engine")
    def test_tpex_daily_returns_unified_format(self, mock_get_engine):
        """確認 TPEX 日線資料回傳統一格式。"""
        row = {
            "date": "2024-01-02",
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 5000,
        }

        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value = [row]
        mock_conn.execute.return_value = mock_result

        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_engine.connect.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_get_engine.return_value = mock_engine

        results = stock_service.get_stock_daily(
            "TPEX", "6510", "2024-01-01", "2024-01-31"
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["close"], 103.0)

    def test_invalid_market_returns_empty(self):
        """確認不支援的市場回傳空列表。"""
        results = stock_service.get_stock_daily(
            "INVALID", "0000", "2024-01-01", "2024-01-31"
        )
        self.assertEqual(results, [])


class TestGetDateRange(unittest.TestCase):
    """get_date_range 測試。"""

    def setUp(self):
        """重設 engine。"""
        stock_service.reset_engine()

    def tearDown(self):
        """重設 engine。"""
        stock_service.reset_engine()

    @patch("tw_stock_indicator.services.stock_service.get_db_engine")
    def test_date_range_returns_min_max(self, mock_get_engine):
        """確認回傳最早與最晚日期。"""
        row = {"min_date": "2020-01-02", "max_date": "2024-12-31"}

        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = row
        mock_conn.execute.return_value = mock_result

        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_engine.connect.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_get_engine.return_value = mock_engine

        result = stock_service.get_date_range("TWSE", "2330")

        self.assertEqual(result["min_date"], "2020-01-02")
        self.assertEqual(result["max_date"], "2024-12-31")

    def test_invalid_market_returns_none(self):
        """確認不支援的市場回傳 None。"""
        result = stock_service.get_date_range("INVALID", "0000")
        self.assertIsNone(result["min_date"])
        self.assertIsNone(result["max_date"])


if __name__ == "__main__":
    unittest.main()
