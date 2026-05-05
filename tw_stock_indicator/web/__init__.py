"""Flask 應用程式工廠模組。"""

import os

from flask import Flask

from tw_stock_indicator.services import rule_service


class ScriptNameMiddleware:
    """WSGI 中介層，為反向代理設定 SCRIPT_NAME。

    當 Flask 應用程式部署於反向代理底下（例如 Dashboard LaunchPad
    將 `/app/indicator/*` 轉發至本服務根路徑）時，SCRIPT_NAME 必須
    設為反向代理掛載的前綴，`url_for()` 才會產生帶前綴的 URL，
    瀏覽器後續請求才會走回反向代理。

    Attributes:
        app: 被包裹的 WSGI application。
        script_name: 反向代理掛載的前綴路徑（例如 `/app/indicator`）。
    """

    def __init__(self, app, script_name: str) -> None:
        """初始化中介層。

        Args:
            app: 被包裹的 WSGI application。
            script_name: SCRIPT_NAME 前綴字串，需以 `/` 開頭、不以 `/` 結尾。
        """
        self.app = app
        self.script_name = script_name

    def __call__(self, environ, start_response):
        """攔截 WSGI 呼叫並注入 SCRIPT_NAME。"""
        environ["SCRIPT_NAME"] = self.script_name
        path_info = environ.get("PATH_INFO", "")
        if path_info.startswith(self.script_name):
            environ["PATH_INFO"] = path_info[len(self.script_name):] or "/"
        return self.app(environ, start_response)


def create_app() -> Flask:
    """建立並設定 Flask 應用程式。

    透過環境變數 `SCRIPT_NAME` 控制反向代理掛載前綴，預設為
    `/app/indicator`，可設為空字串以本地直連模式執行。

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

    # 套用反向代理 SCRIPT_NAME 中介層
    script_name = os.environ.get("SCRIPT_NAME", "/app/indicator")
    if script_name:
        app.wsgi_app = ScriptNameMiddleware(app.wsgi_app, script_name)

    return app
