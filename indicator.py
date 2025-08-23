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
        self.total_profit = self.cal_total_profit()
        self.total_trade_times = self.cal_total_trade_times()
        self.mean_profit = self.cal_mean_profit()
        self.mean_holding_days = self.cal_mean_holding_days()
        self.earn_rate = self.cal_earn_rate()
        self.loss_rate = self.cal_loss_rate()
        self.mean_earn = self.cal_mean_earn()
        self.mean_loss = self.cal_mean_loss()
        self.earn_loss_odds = self.cal_earn_loss_odds()
        self.expect_profit = self.cal_expect_profit()
        self.mean_earn_open_days = self.cal_mean_earn_open_days()

    def _validate_stock_type(self, stock_type):
        """
        Validate the stock type.
        """
        if stock_type not in ["Stock", "ETF"]:
            raise ValueError("stock_type must be either 'Stock' or 'ETF'.")
        return stock_type
    
    def cal_total_profit(self):
        """
        Calculate the profit from the trade data.

        Returns:
            float: The total profit from the trades.
        """
        if self.trade.empty:
            return 0.0

        profit = np.sum(self.trade['cover_price'] - self.trade['order_price'])
        if self.stock_type == 'ETF':
            profit *= 1 - (0.001 + 0.00285)
        
        elif self.stock_type == 'Stock':
            profit *= 1 - (0.003 + 0.00285)

        else:
            raise ValueError("Invalid stock type. Must be either 'Stock' or 'ETF'.")
        return profit

    def cal_total_trade_times(self):
        """
        Calculate the total number of trades.

        Returns:
            int: The total number of trades.
        """
        if self.trade.empty:
            return 0

        return self.trade.shape[0]
    
    def cal_mean_profit(self):
        """
        Calculate the mean profit per trade.

        Returns:
            float: The mean profit per trade.
        """
        if self.trade.empty:
            return 0.0

        total_profit = self.total_profit
        total_trades = self.total_trade_time

        if total_trades == 0:
            return 0.0

        return total_profit / total_trades
    
    def cal_mean_holding_days(self):
        """
        Calculate the mean holding days for the trades.

        Returns:
            float: The mean holding days.
        """
        if self.trade.empty:
            return 0.0

        holding_days = (self.trade['cover_day'] - self.trade['order_day']).dt.days
        return holding_days.mean()
    
    def cal_earn_rate(self):
        """
        Calculate the earning rate based on the total profit and the initial investment.

        Returns:
            float: The earning rate.
        """
        if self.trade.empty:
            return 0.0

        earn_times = np.sum(self.trade['cover_day']>self.trade['order_day'])
        return earn_times / self.total_trade_times
    
    def cal_loss_rate(self):
        """
        Calculate the loss rate based on the total trades and the number of losing trades.

        Returns:
            float: The loss rate.
        """
        if self.trade.empty:
            return 0.0

        losing_trades = np.sum(self.trade['cover_price'] <= self.trade['order_price'])
        return losing_trades / self.total_trade_times 
    
    def cal_mean_earn(self):
        """
        Calculate the mean earning from the trades.

        Returns:
            float: The mean earning.
        """
        if self.trade.empty:
            return 0.0

        earn_times = np.sum(self.trade['cover_day'] > self.trade['order_day'])
        total_profit = np.sum(self.trade['cover_price'] - self.trade['order_price'])
        
        if earn_times == 0:
            return 0.0
        
        return total_profit / earn_times
    
    def cal_mean_loss(self):
        """
        Calculate the mean loss from the trades.

        Returns:
            float: The mean loss.
        """
        if self.trade.empty:
            return 0.0

        losing_times = np.sum(self.trade['cover_price'] <= self.trade['order_price'])
        total_loss = np.sum(self.trade['order_price'] - self.trade['cover_price'])

        if losing_times == 0:
            return 0.0
        
        return total_loss / losing_times
    
    def cal_earn_loss_odds(self):
        """
        Calculate the earning to losing odds.

        Returns:
            float: The earning to losing odds.
        """
        if self.trade.empty:
            return 0.0

        earn_times = np.sum(self.trade['cover_day'] > self.trade['order_day'])
        losing_times = np.sum(self.trade['cover_price'] <= self.trade['order_price'])

        if losing_times == 0:
            return float('inf')

        return earn_times / losing_times
    
    def cal_expect_profit(self):
        """
        Calculate the expected profit based on the mean profit and the total trade times.

        Returns:
            float: The expected profit.
        """
        if self.trade.empty:
            return 0.0

        return self.mean_profit * self.total_trade_times
    
    def cal_mean_earn_open_days(self):
        """
        Calculate the number of days when the stock was open for trading.

        Returns:
            int: The number of open days.
        """
        if self.trade.empty:
            return 0

        earn_df = self.trade['order_price'] < self.trade['cover_price']
        days = earn_df["cover_day"] - earn_df["order_day"]
        return np.mean(days)
    
    def cal_