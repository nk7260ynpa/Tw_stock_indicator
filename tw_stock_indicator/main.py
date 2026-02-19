"""程式進入點。

初始化 logger 並作為未來技術指標功能的入口。
"""

from tw_stock_indicator import __version__
from tw_stock_indicator.logger import setup_logger


def main() -> None:
    """主程式入口。"""
    logger = setup_logger()
    logger.info("Tw Stock Indicator v%s 啟動", __version__)
    logger.info("程式執行完畢")


if __name__ == "__main__":
    main()
