"""Flask 路由與 API 單元測試。"""

import json
import unittest

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

    def test_index_contains_indicators(self):
        """確認首頁包含指標資訊。"""
        resp = self.client.get("/")
        html = resp.data.decode("utf-8")
        self.assertIn("勝率", html)
        self.assertIn("獲利因子", html)
        self.assertIn("62.5%", html)

    def test_index_contains_rule_designer(self):
        """確認首頁包含規則設計器。"""
        resp = self.client.get("/")
        html = resp.data.decode("utf-8")
        self.assertIn("rule-designer", html)


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


if __name__ == "__main__":
    unittest.main()
