import numpy as np
import pandas as pd

class StockIndicator():
    def __init__(self, trade, start_date, end_date, stock_type='stock'):
        """
        Initialize the StockIndicator with the given parameters.
        Args:
            trade (pd.DataFrame): The trade data containing order and cover times.
                contains columns 'order_day', 'cover_day', 'order_price', 'cover_price'.
            start_date (str): The start date for the stock data.
            end_date (str): The end date for the stock data.
            stock_type (str, optional): The type of stock. Defaults to 'stock'.
        """
        self.trade = trade
        self.start_date = start_date
        self.end_date = end_date
        self.stock_type = self._validate_stock_type(stock_type)

    def _validate_stock_type(self, stock_type):
        if stock_type not in ["Stock", "ETF"]:
            raise ValueError("stock_type must be either 'Stock' or 'ETF'.")
        return stock_type
    
    def total_calculate_profit(self):
        """
        Calculate the profit from the trade data.
        Returns:
            pd.DataFrame: A DataFrame containing the profit for each trade.
        """
        if self.trade.empty:
            return 0.0

        profit = np.sum(self.trade['cover_price'] - self.trade['order_price'])
        return profit
    