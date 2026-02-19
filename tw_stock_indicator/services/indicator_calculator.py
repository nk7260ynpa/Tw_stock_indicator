"""技術指標計算模組。

純 Python 實作 MA、RSI、MACD、KD、布林通道等技術指標計算。
"""

import math


def calc_ma(closes: list[float], period: int) -> list[float | None]:
    """計算簡單移動平均線（SMA）。

    Args:
        closes: 收盤價序列。
        period: 移動平均期數。

    Returns:
        與 closes 等長的列表，暖機期不足的位置為 None。
    """
    n = len(closes)
    result: list[float | None] = [None] * n
    if period <= 0 or n < period:
        return result

    window_sum = sum(closes[:period])
    result[period - 1] = window_sum / period

    for i in range(period, n):
        window_sum += closes[i] - closes[i - period]
        result[i] = window_sum / period

    return result


def calc_rsi(closes: list[float], period: int) -> list[float | None]:
    """計算 RSI（Wilder 平滑法）。

    Args:
        closes: 收盤價序列。
        period: RSI 期數。

    Returns:
        與 closes 等長的列表，暖機期不足的位置為 None。
    """
    n = len(closes)
    result: list[float | None] = [None] * n
    if period <= 0 or n < period + 1:
        return result

    gains = []
    losses = []
    for i in range(1, n):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))

    # 初始平均值（前 period 根的簡單平均）
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        result[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        result[period] = 100.0 - 100.0 / (1.0 + rs)

    # Wilder 平滑
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            result[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i + 1] = 100.0 - 100.0 / (1.0 + rs)

    return result


def calc_macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, list[float | None]]:
    """計算 MACD 指標。

    Args:
        closes: 收盤價序列。
        fast: 快線 EMA 期數。
        slow: 慢線 EMA 期數。
        signal: 訊號線 EMA 期數。

    Returns:
        包含 DIF、MACD、OSC 序列的字典。
    """
    n = len(closes)
    dif: list[float | None] = [None] * n
    macd_line: list[float | None] = [None] * n
    osc: list[float | None] = [None] * n

    if n < slow:
        return {"DIF": dif, "MACD": macd_line, "OSC": osc}

    # 計算 EMA
    def _ema(data: list[float], period: int) -> list[float | None]:
        result_ema: list[float | None] = [None] * len(data)
        if len(data) < period:
            return result_ema
        # 初始值為前 period 根的 SMA
        sma = sum(data[:period]) / period
        result_ema[period - 1] = sma
        multiplier = 2.0 / (period + 1)
        for i in range(period, len(data)):
            result_ema[i] = (data[i] - result_ema[i - 1]) * multiplier + result_ema[i - 1]
        return result_ema

    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)

    # DIF = 快線 EMA - 慢線 EMA
    dif_values: list[float] = []
    for i in range(n):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            dif[i] = ema_fast[i] - ema_slow[i]
            dif_values.append(dif[i])

    # MACD（訊號線）= DIF 的 EMA
    if len(dif_values) >= signal:
        dif_start = n - len(dif_values)
        macd_vals = _ema(dif_values, signal)
        for i, val in enumerate(macd_vals):
            idx = dif_start + i
            macd_line[idx] = val
            if val is not None and dif[idx] is not None:
                osc[idx] = (dif[idx] - val) * 2

    return {"DIF": dif, "MACD": macd_line, "OSC": osc}


def calc_kd(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 9,
    smooth: int = 3,
) -> dict[str, list[float | None]]:
    """計算 KD 指標（隨機指標）。

    Args:
        highs: 最高價序列。
        lows: 最低價序列。
        closes: 收盤價序列。
        period: RSV 回看期數。
        smooth: K、D 平滑期數。

    Returns:
        包含 K、D 序列的字典。
    """
    n = len(closes)
    k_vals: list[float | None] = [None] * n
    d_vals: list[float | None] = [None] * n

    if n < period:
        return {"K": k_vals, "D": d_vals}

    # 計算 RSV
    rsv: list[float | None] = [None] * n
    for i in range(period - 1, n):
        highest = max(highs[i - period + 1:i + 1])
        lowest = min(lows[i - period + 1:i + 1])
        if highest == lowest:
            rsv[i] = 50.0
        else:
            rsv[i] = (closes[i] - lowest) / (highest - lowest) * 100.0

    # K、D 平滑（遞迴平滑法）
    k_prev = 50.0
    d_prev = 50.0
    for i in range(period - 1, n):
        if rsv[i] is not None:
            k_val = (k_prev * (smooth - 1) + rsv[i]) / smooth
            d_val = (d_prev * (smooth - 1) + k_val) / smooth
            k_vals[i] = round(k_val, 2)
            d_vals[i] = round(d_val, 2)
            k_prev = k_val
            d_prev = d_val

    return {"K": k_vals, "D": d_vals}


def calc_bollinger(
    closes: list[float],
    period: int = 20,
    std_dev: float = 2.0,
) -> dict[str, list[float | None]]:
    """計算布林通道。

    Args:
        closes: 收盤價序列。
        period: 移動平均期數。
        std_dev: 標準差倍數。

    Returns:
        包含上軌、中軌、下軌序列的字典。
    """
    n = len(closes)
    upper: list[float | None] = [None] * n
    middle: list[float | None] = [None] * n
    lower: list[float | None] = [None] * n

    if n < period:
        return {"上軌": upper, "中軌": middle, "下軌": lower}

    for i in range(period - 1, n):
        window = closes[i - period + 1:i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(variance)

        middle[i] = mean
        upper[i] = mean + std_dev * std
        lower[i] = mean - std_dev * std

    return {"上軌": upper, "中軌": middle, "下軌": lower}


def build_indicator_series(
    daily_data: list[dict],
) -> dict[str, list[float | None]]:
    """根據日線資料建立所有技術指標序列。

    Args:
        daily_data: 日線資料列表，每筆包含 open、high、low、close 欄位。

    Returns:
        指標名稱到序列的字典，key 對應 rule_service 中的參數名稱。
    """
    closes = [d["close"] for d in daily_data]
    highs = [d["high"] for d in daily_data]
    lows = [d["low"] for d in daily_data]
    n = len(closes)

    series: dict[str, list[float | None]] = {}

    # 收盤價
    series["收盤價"] = list(closes)

    # MA
    for period in (5, 10, 20, 60, 120, 240):
        series[f"MA{period}"] = calc_ma(closes, period)

    # RSI
    for period in (6, 12, 24):
        series[f"RSI{period}"] = calc_rsi(closes, period)

    # MACD
    macd = calc_macd(closes)
    series["DIF"] = macd["DIF"]
    series["MACD"] = macd["MACD"]
    series["OSC"] = macd["OSC"]

    # KD
    kd = calc_kd(highs, lows, closes)
    series["K"] = kd["K"]
    series["D"] = kd["D"]

    # 布林通道
    boll = calc_bollinger(closes)
    series["上軌"] = boll["上軌"]
    series["中軌"] = boll["中軌"]
    series["下軌"] = boll["下軌"]

    # 常數序列（用於規則比較）
    for const in (0, 20, 30, 50, 70, 80):
        series[str(const)] = [float(const)] * n

    return series
