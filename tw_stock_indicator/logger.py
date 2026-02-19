"""日誌配置模組。

提供統一的 logging 設定，同時輸出至 console 與 logs/ 目錄下的檔案。
"""

import logging
import os
from datetime import datetime


def setup_logger(name: str = "tw_stock_indicator") -> logging.Logger:
    """建立並回傳已配置的 logger。

    Args:
        name: logger 名稱，預設為 'tw_stock_indicator'。

    Returns:
        已設定 console 與 file handler 的 Logger 物件。
    """
    logger = logging.getLogger(name)

    # 避免重複加入 handler
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_filename = datetime.now().strftime("%Y%m%d") + ".log"
    log_path = os.path.join(log_dir, log_filename)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
