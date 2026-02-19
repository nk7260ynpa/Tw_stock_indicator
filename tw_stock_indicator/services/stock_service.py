"""股票資料查詢服務。

提供從 MySQL 資料庫查詢股票名稱與日線資料的功能。
"""

import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_engine: Engine | None = None


def get_db_engine() -> Engine:
    """建立或取得 SQLAlchemy engine。

    從環境變數 DB_HOST、DB_USER、DB_PASSWORD 讀取連線資訊，
    連接至 MySQL 資料庫。

    Returns:
        SQLAlchemy Engine 實例。
    """
    global _engine
    if _engine is not None:
        return _engine

    host = os.environ.get("DB_HOST", "localhost")
    user = os.environ.get("DB_USER", "root")
    password = os.environ.get("DB_PASSWORD", "")
    port = os.environ.get("DB_PORT", "3306")

    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/"
    _engine = create_engine(url, pool_pre_ping=True)
    logger.info("資料庫連線建立完成: %s:%s", host, port)
    return _engine


def reset_engine() -> None:
    """重設 engine（供測試使用）。"""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def search_stocks(keyword: str) -> list[dict]:
    """搜尋股票代碼或名稱。

    同時查詢 TWSE.StockName 與 TPEX.StockName，
    支援代碼或名稱模糊搜尋。

    Args:
        keyword: 搜尋關鍵字（代碼或名稱）。

    Returns:
        符合的股票列表，每筆包含 code、name、market 欄位。
    """
    engine = get_db_engine()
    results = []
    like_pattern = f"%{keyword}%"

    twse_query = text(
        "SELECT SecurityCode AS code, StockName AS name "
        "FROM TWSE.StockName "
        "WHERE SecurityCode LIKE :pattern OR StockName LIKE :pattern "
        "LIMIT 20"
    )

    tpex_query = text(
        "SELECT Code AS code, Name AS name "
        "FROM TPEX.StockName "
        "WHERE Code LIKE :pattern OR Name LIKE :pattern "
        "LIMIT 20"
    )

    with engine.connect() as conn:
        rows = conn.execute(twse_query, {"pattern": like_pattern})
        for row in rows.mappings():
            results.append({
                "code": row["code"].strip(),
                "name": row["name"].strip(),
                "market": "TWSE",
            })

        rows = conn.execute(tpex_query, {"pattern": like_pattern})
        for row in rows.mappings():
            results.append({
                "code": row["code"].strip(),
                "name": row["name"].strip(),
                "market": "TPEX",
            })

    return results


def get_stock_daily(
    market: str,
    code: str,
    start_date: str,
    end_date: str,
) -> list[dict]:
    """查詢指定股票的日線資料。

    根據 market 決定查詢 TWSE.DailyPrice 或 TPEX.DailyPrice，
    統一回傳格式。

    Args:
        market: 市場別（TWSE 或 TPEX）。
        code: 股票代碼。
        start_date: 起始日期（YYYY-MM-DD）。
        end_date: 結束日期（YYYY-MM-DD）。

    Returns:
        日線資料列表，每筆包含 date、open、high、low、close、volume。
    """
    engine = get_db_engine()

    if market == "TWSE":
        query = text(
            "SELECT Date AS date, "
            "OpeningPrice AS open, HighestPrice AS high, "
            "LowestPrice AS low, ClosingPrice AS close, "
            "TradeVolume AS volume "
            "FROM TWSE.DailyPrice "
            "WHERE SecurityCode = :code "
            "AND Date BETWEEN :start AND :end "
            "ORDER BY Date"
        )
    elif market == "TPEX":
        query = text(
            "SELECT Date AS date, "
            "`Open` AS open, High AS high, "
            "Low AS low, `Close` AS close, "
            "TradeVolume AS volume "
            "FROM TPEX.DailyPrice "
            "WHERE Code = :code "
            "AND Date BETWEEN :start AND :end "
            "ORDER BY Date"
        )
    else:
        logger.warning("不支援的市場別: %s", market)
        return []

    with engine.connect() as conn:
        rows = conn.execute(
            query, {"code": code, "start": start_date, "end": end_date}
        )
        results = []
        for row in rows.mappings():
            results.append({
                "date": str(row["date"]),
                "open": float(row["open"]) if row["open"] else None,
                "high": float(row["high"]) if row["high"] else None,
                "low": float(row["low"]) if row["low"] else None,
                "close": float(row["close"]) if row["close"] else None,
                "volume": int(row["volume"]) if row["volume"] else None,
            })

    return results


def get_date_range(market: str, code: str) -> dict:
    """取得指定股票可查詢的日期範圍。

    Args:
        market: 市場別（TWSE 或 TPEX）。
        code: 股票代碼。

    Returns:
        包含 min_date 與 max_date 的字典。
    """
    engine = get_db_engine()

    if market == "TWSE":
        query = text(
            "SELECT MIN(Date) AS min_date, MAX(Date) AS max_date "
            "FROM TWSE.DailyPrice "
            "WHERE SecurityCode = :code"
        )
    elif market == "TPEX":
        query = text(
            "SELECT MIN(Date) AS min_date, MAX(Date) AS max_date "
            "FROM TPEX.DailyPrice "
            "WHERE Code = :code"
        )
    else:
        return {"min_date": None, "max_date": None}

    with engine.connect() as conn:
        row = conn.execute(query, {"code": code}).mappings().first()
        if row and row["min_date"]:
            return {
                "min_date": str(row["min_date"]),
                "max_date": str(row["max_date"]),
            }

    return {"min_date": None, "max_date": None}
