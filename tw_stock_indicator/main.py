"""程式進入點。

初始化 logger，支援 --web 啟動 Flask 儀表板。
"""

import argparse

from tw_stock_indicator import __version__
from tw_stock_indicator.logger import setup_logger


def parse_args() -> argparse.Namespace:
    """解析命令列參數。

    Returns:
        解析後的參數命名空間。
    """
    parser = argparse.ArgumentParser(description="台灣股票技術指標分析工具")
    parser.add_argument(
        "--web", action="store_true", help="啟動 Web 儀表板",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Web 伺服器綁定位址（預設 0.0.0.0）",
    )
    parser.add_argument(
        "--port", type=int, default=5001, help="Web 伺服器埠號（預設 5001）",
    )
    return parser.parse_args()


def main() -> None:
    """主程式入口。"""
    logger = setup_logger()
    args = parse_args()

    logger.info("Tw Stock Indicator v%s 啟動", __version__)

    if args.web:
        from tw_stock_indicator.web import create_app

        app = create_app()
        logger.info("啟動 Web 儀表板於 %s:%d", args.host, args.port)
        app.run(host=args.host, port=args.port, debug=False)
    else:
        logger.info("程式執行完畢")


if __name__ == "__main__":
    main()
