import pandas as pd
from talib.abstract import RSI

from .base import BaseStrategy

class RSIExceedStrategy(BaseStrategy):
    """
    Relative Strength Index Exceed Strategy:
    Buy when the RSI exceeds 60.
    Sell when the RSI drops below 60.

    Args:
    def __init__(self):
        super().__init__()
        self.order_day = None
        self.order_price = None
        self.trades = pd.DataFrame(columns=["order_day", "cover_day", "order_price", "cover_price"])    

    Returns:
        pd.DataFrame: A DataFrame containing the trade records with columns:
            'order_day', 'cover_day', 'order_price', 'cover_price'.
    """
    def __call__(self, data):
        data["RSI1"] = RSI(data, timeperiod=10)
        data["RSI2"] = RSI(data, timeperiod=15)
        over_buy = 60
        over_sell = 40
        rsi_min, rsi_min_time = 100, 0
        for i in range(data.shape[0]-1):
            c_time = data.index[i]
            c_low = data.loc[c_time, 'low']
            c_high = data.loc[c_time, 'high']
            c_close = data.loc[c_time, 'close']
            c_open = data.loc[c_time, 'open']
            c_rsi1 = data.loc[c_time, 'RSI1']
            c_rsi2 = data.loc[c_time, 'RSI2']
            n_time = data.index[i+1]
            n_open = data.loc[n_time, 'open']

            if self.order_day is None:
                if c_rsi1 > c_rsi2:
                    self.order_day = n_time
                    self.order_price = n_open

            elif self.order_day is not None and c_rsi1 < c_rsi2*0.999:
                new_trade = pd.DataFrame([{
                    "order_day": self.order_day,
                    "cover_day": n_time,
                    "order_price": self.order_price,
                    "cover_price": n_open
                }])
                self.trades = pd.concat([self.trades, new_trade], ignore_index=True)
                self.cover_order()
        return self.trades