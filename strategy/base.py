from abc import ABC, abstractmethod

import pandas as pd

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

