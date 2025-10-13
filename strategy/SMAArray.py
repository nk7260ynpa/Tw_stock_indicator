import pandas as pd
from talib.abstract import SMA

from .base import BaseStrategy

class SMAExceedStrategy(BaseStrategy):
    """
    Simple Moving Average Exceed Strategy:
    Buy when the price exceeds the simple moving average by a certain threshold.
    Sell when the price drops below the simple moving average by a certain threshold.

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
        data["SMA1"] = SMA(data, timeperiod=5)
        data["SMA2"] = SMA(data, timeperiod=10)
        data["SMA3"] = SMA(data, timeperiod=30)
        for i in range(data.shape[0]-1):
            c_time = data.index[i]
            c_low = data.loc[c_time, 'low']
            c_high = data.loc[c_time, 'high']
            c_close = data.loc[c_time, 'close']
            c_open = data.loc[c_time, 'open']
            c_sma1 = data.loc[c_time, 'SMA1']
            c_sma2 = data.loc[c_time, 'SMA2']
            c_sma3 = data.loc[c_time, 'SMA3']

            n_time = data.index[i+1]
            n_open = data.loc[n_time, 'open']

            if self.order_day is None and c_sma1 > c_sma2 > c_sma3:
                self.order_day = n_time
                self.order_price = n_open
            
            elif self.order_day is not None and not c_sma1 > c_sma2 > c_sma3:
                new_trade = pd.DataFrame([{
                    "order_day": self.order_day,
                    "cover_day": n_time,
                    "order_price": self.order_price,
                    "cover_price": n_open
                }])
                self.trades = pd.concat([self.trades, new_trade], ignore_index=True)
                self.cover_order()
        return self.trades