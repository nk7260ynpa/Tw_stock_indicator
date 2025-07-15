import numpy as np
import pandas as pd

class StockIndicator:
    def __init__(self, code, trade, data, stock_type='stock'):
        """
        Initialize the StockIndicator with the given parameters.

        Args:
            start_date (str): The start date for the stock data.
            end_date (str): The end date for the stock data.
            code (str): The stock code.
            stock_type (str, optional): The type of stock. Defaults to 'stock'.
        """
        self.code = code
        self.trade = trade
        self.stock_type = stock_type
        self.tax_rate = self._get_tax_rate()
        self.data = data
        self.total_profit_rate = self._get_total_profit_rate()
        self.trade_times = self._get_trade_times()
        self.average_profit_rate = self._get_average_profit_rate()
        self.onopen_days = self._get_onopen_days()
        self.earn_rate = self._get_earn_rate()
        self.earn_total_profit_rate = self._get_earn_total_profit_rate()
        self.loss_total_profit_rate = self._get_loss_total_profit_rate()
        self.total_odds = self._get_total_odds()

    def _data_preprocess(self):
        """
        Preprocess the stock data to ensure it is in the correct format.
        
        This method should be called before any calculations are performed.
        """
        if not isinstance(self.data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame.")
        if 'date' not in self.data.columns:
            raise ValueError("Data must contain a 'date' column.")
        self.data["profit_rate"] = (self.data["close"] - self.data["open"]) / self.data["open"] - self.tax_rate

    def _get_tax_rate(self):
        """
        Get the tax rate based on the stock type.

        Returns:
            float: The tax rate for the stock type.
        """
        if self.stock_type == 'stock':
            return 0.003 + 0.00285
        elif self.stock_type == 'eft':
            return 0.001 + 0.00285
        else:
            raise ValueError("Invalid stock type. Must be 'stock' or 'etf'.")
        
    def _get_total_profit_rate(self):
        """
        Calculate the profit rate based on the trade data.
        
        Returns:
            float: The profit rate calculated from the trade data.
        """
        return np.sum(self.data["profit_rate"])

    def _get_trade_times(self):
        """
        Get the number of trade times

        Returns:
            int: The number of trade times
        """
        return self.trade.shape[0]
    
    def _get_average_profit_rate(self):
        """
        Get the average profit rate.

        Returns:
            float: The average profit rate.
        """
        if self.trade_times == 0:
            return 0.0
        return self.profit_rate / self.trade_times
    
    def _get_onopen_days(self):
        """
        Get the number of days the stock was open.

        Returns:
            int: The number of open days.
        """
        return (self.trade["cover_time"] - self.trade["order_time"]).dt.days
    
    def _get_earn_rate(self):
        """
        Calculate the earn rate based on the profit rate and the number of trade times.

        Returns:
            float: The earn rate.
        """
        if self.trade_times == 0:
            return 0.0
        earn_rate = self.data["profit_rate"] > 0 / self.trade.shape[0]
        return earn_rate
    
    def _get_earn_total_profit_rate(self):
        """
        Calculate the total profit rate for the earn trades.

        Returns:
            float: The total profit rate for the earn trades.
        """
        if self.trade_times == 0:
            return 0.0
        earn_total_profit_rate = self.data[self.data["profit_rate"] > 0]["profit_rate"].sum() / self.trade.shape[0]
        return earn_total_profit_rate
    
    def _get_loss_total_profit_rate(self):
        """
        Calculate the total profit rate for the loss trades.

        Returns:
            float: The total profit rate for the loss trades.
        """
        if self.trade_times == 0:
            return 0.0
        loss_total_profit_rate = self.data[self.data["profit_rate"] <= 0]["profit_rate"].sum() / self.trade.shape[0]
        return loss_total_profit_rate
    
    def _get_total_odds(self):
        """
        Calculate the total odds based on the profit rate and the number of trade times.

        Returns:
            float: The total odds.
        """
        if self.trade_times == 0:
            return 0.0
        return  abs(self.earn_total_profit_rate / self.loss_total_profit_rate) 
