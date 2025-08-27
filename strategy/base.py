from abc import ABC, abstractmethod

import pandas as pd
from talib.abstract import EMA

class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    """
    def __init__(self):
        self.trades = pd.DataFrame(columns=["order_day", "cover_day", 
                                            "order_price", "cover_price"])
        self.order_day = None
        self.order_price = None
    
    def place_order(self, day, price):
        """
        Place an order to buy a stock.

        Args:
            day (str): The day of the order.
            price (float): The price of the stock at the time of order.
        """
        self.order_day = day
        self.order_price = price

    def cover_order(self):
        self.order_day = None
        self.order_price = None

    @abstractmethod
    def __call__(self, price_df):
        pass

class MAExceedStrategy(BaseStrategy):
    """
    Moving Average Exceed Strategy:
    Buy when the price exceeds the moving average by a certain threshold.
    Sell when the price drops below the moving average by a certain threshold.
    """
    def __call__(self, data):
        data["EMA"] = EMA(data, timeperiod=5)
        for i in range(data.shape[0]-1):
            c_time = data.index[i]
            c_low = data.loc[c_time, 'low']
            c_high = data.loc[c_time, 'high']
            c_close = data.loc[c_time, 'close']
            c_open = data.loc[c_time, 'open']
            c_ema = data.loc[c_time, 'EMA']

            n_time = data.index[i+1]
            n_open = data.loc[n_time, 'open']