"""API 路由。

提供規則 CRUD、指標參數查詢與股票資料查詢的 RESTful API。
"""

import logging
from dataclasses import asdict

from flask import Blueprint, jsonify, request

from tw_stock_indicator.models.rules import IndicatorType, LogicOperator, Operator
from tw_stock_indicator.services import backtest_service, rule_service, stock_service

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/indicators/<indicator_type>/params")
def get_indicator_params(indicator_type: str):
    """取得指標可選參數。"""
    try:
        it = IndicatorType(indicator_type)
    except ValueError:
        return jsonify({"error": f"未知的指標類型: {indicator_type}"}), 400

    params = rule_service.get_indicator_params(it)
    return jsonify({"params": params})


@api_bp.route("/rules")
def list_rules():
    """列出所有規則群組。"""
    groups = rule_service.get_all_rule_groups()
    result = []
    for g in groups:
        result.append({
            "id": g.id,
            "name": g.name,
            "rule_type": g.rule_type,
            "conditions": [asdict(c) for c in g.conditions],
            "logic_operators": [lo.value for lo in g.logic_operators],
        })
    return jsonify(result)


@api_bp.route("/rules", methods=["POST"])
def create_rule():
    """建立規則群組。"""
    data = request.get_json()
    if not data or "name" not in data or "rule_type" not in data:
        return jsonify({"error": "需要 name 和 rule_type 欄位"}), 400

    if data["rule_type"] not in ("entry", "exit"):
        return jsonify({"error": "rule_type 必須為 entry 或 exit"}), 400

    group = rule_service.create_rule_group(data["name"], data["rule_type"])
    return jsonify({"id": group.id, "name": group.name, "rule_type": group.rule_type}), 201


@api_bp.route("/rules/<group_id>/conditions", methods=["POST"])
def add_condition(group_id: str):
    """新增條件至規則群組。"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "缺少請求內容"}), 400

    required = ["indicator_type", "left_param", "operator", "right_param"]
    for field_name in required:
        if field_name not in data:
            return jsonify({"error": f"缺少欄位: {field_name}"}), 400

    try:
        indicator_type = IndicatorType(data["indicator_type"])
        operator = Operator(data["operator"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    logic_op = LogicOperator.AND
    if "logic_operator" in data:
        try:
            logic_op = LogicOperator(data["logic_operator"])
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    condition = rule_service.add_condition(
        group_id, indicator_type, data["left_param"], operator,
        data["right_param"], logic_op,
    )

    if condition is None:
        return jsonify({"error": "規則群組不存在"}), 404

    return jsonify({
        "id": condition.id,
        "indicator_type": condition.indicator_type.value,
        "left_param": condition.left_param,
        "operator": condition.operator.value,
        "right_param": condition.right_param,
    }), 201


@api_bp.route("/rules/<group_id>/conditions/<condition_id>", methods=["DELETE"])
def delete_condition(group_id: str, condition_id: str):
    """刪除規則群組中的條件。"""
    success = rule_service.remove_condition(group_id, condition_id)
    if not success:
        return jsonify({"error": "規則群組或條件不存在"}), 404
    return jsonify({"message": "條件已刪除"})


# --- 股票資料 API ---


@api_bp.route("/stocks/search")
def search_stocks():
    """搜尋股票代碼或名稱。"""
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify([])

    try:
        results = stock_service.search_stocks(keyword)
    except Exception:
        logger.exception("股票搜尋失敗")
        return jsonify({"error": "資料庫查詢失敗"}), 500

    return jsonify(results)


@api_bp.route("/stocks/<market>/<code>/daily")
def get_stock_daily(market: str, code: str):
    """取得指定股票的日線資料。"""
    market = market.upper()
    if market not in ("TWSE", "TPEX"):
        return jsonify({"error": "market 必須為 TWSE 或 TPEX"}), 400

    start = request.args.get("start", "")
    end = request.args.get("end", "")
    if not start or not end:
        return jsonify({"error": "需要 start 和 end 參數"}), 400

    try:
        data = stock_service.get_stock_daily(market, code, start, end)
    except Exception:
        logger.exception("股價查詢失敗")
        return jsonify({"error": "資料庫查詢失敗"}), 500

    return jsonify(data)


@api_bp.route("/backtest", methods=["POST"])
def run_backtest():
    """執行回測計算。"""
    data = request.get_json()
    if not data or "daily_data" not in data:
        return jsonify({"error": "缺少 daily_data 欄位"}), 400

    daily_data = data["daily_data"]
    if not daily_data or len(daily_data) < 2:
        return jsonify({"error": "日線資料不足（至少需要 2 筆）"}), 400

    shares = data.get("shares", 1000)

    rule_groups = rule_service.get_all_rule_groups()
    if not rule_groups:
        return jsonify({"error": "尚未設定進出場規則"}), 400

    try:
        backtest_result = backtest_service.run_backtest(
            daily_data, rule_groups, shares
        )
    except Exception:
        logger.exception("回測計算失敗")
        return jsonify({"error": "回測計算失敗"}), 500

    indicators = []
    for ind in backtest_result["indicators"]:
        indicators.append({
            "code": ind.code,
            "name": ind.name,
            "value": ind.value,
            "unit": ind.unit,
            "description": ind.description,
            "formatted_value": ind.formatted_value(),
        })

    return jsonify({
        "indicators": indicators,
        "trades": backtest_result["trades"],
        "indicator_series": backtest_result["indicator_series"],
    })


@api_bp.route("/stocks/<market>/<code>/date-range")
def get_stock_date_range(market: str, code: str):
    """取得指定股票可查詢的日期範圍。"""
    market = market.upper()
    if market not in ("TWSE", "TPEX"):
        return jsonify({"error": "market 必須為 TWSE 或 TPEX"}), 400

    try:
        result = stock_service.get_date_range(market, code)
    except Exception:
        logger.exception("日期範圍查詢失敗")
        return jsonify({"error": "資料庫查詢失敗"}), 500

    return jsonify(result)
