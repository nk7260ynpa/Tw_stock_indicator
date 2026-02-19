"""Flask 應用程式工廠模組。"""

from flask import Flask

from tw_stock_indicator.services import rule_service


def create_app() -> Flask:
    """建立並設定 Flask 應用程式。

    Returns:
        已註冊藍圖的 Flask app 實例。
    """
    app = Flask(__name__)

    from tw_stock_indicator.web.routes.api import api_bp
    from tw_stock_indicator.web.routes.dashboard import dashboard_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)

    # 載入預設規則
    rule_service.load_default_rules()

    return app
