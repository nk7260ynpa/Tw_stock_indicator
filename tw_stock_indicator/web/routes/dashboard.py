"""儀表板路由。

提供首頁儀表板頁面的路由。
"""

from flask import Blueprint, render_template

from tw_stock_indicator.models.rules import IndicatorType, Operator
from tw_stock_indicator.services import indicator_service, rule_service

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """渲染儀表板首頁。"""
    indicators = indicator_service.get_demo_indicators()
    rule_groups = rule_service.get_all_rule_groups()
    indicator_types = [t.value for t in IndicatorType]
    operators = [o.value for o in Operator]

    return render_template(
        "dashboard.html",
        indicators=indicators,
        rule_groups=rule_groups,
        indicator_types=indicator_types,
        operators=operators,
    )
