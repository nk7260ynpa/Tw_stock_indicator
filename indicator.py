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

    def total_trade_times(self):
        """
        Calculate the total number of trades.

        Returns:
            int: The total number of trades.
        """
        if self.trade.empty:
            return 0

        return self.trade.shape[0]
    
    def mean_profit(self):
        """
        Calculate the mean profit per trade.

        Returns:
            float: The mean profit per trade.
        """
        if self.trade.empty:
            return 0.0

        total_profit = self.total_calculate_profit()
        total_trades = self.total_trade_times()

        if total_trades == 0:
            return 0.0

        return total_profit / total_trades
    
    def win_rate(self):
        """
        Calculate the win rate of the trades.

        Returns:
            float: The win rate as a percentage.
        """
        if self.trade.empty:
            return 0.0

        win_trades = self.trade[self.trade['cover_price'] > self.trade['order_price']]
        total_trades = self.total_trade_times()

        if total_trades == 0:
            return 0.0

        return len(win_trades) / total_trades * 100
    
    def total_holding_days(self):
        """
        Calculate the total holding days for all trades.

        Returns:
            int: The total number of holding days.
        """
        if self.trade.empty:
            return 0

        holding_days = (self.trade['cover_day'] - self.trade['order_day']).sum()
        return holding_days
    
    def cal_win_rate(self):
        """
        Calculate the win rate of the trades.

        Returns:
            float: The win rate as a percentage.
        """
        if self.trade.empty:
            return 0.0

        win_trades = self.trade[self.trade['cover_price'] > self.trade['order_price']]
        total_trades = self.total_trade_times()

        if total_trades == 0:
            return 0.0

        return len(win_trades) / total_trades * 100
    
    def cal_loss_rate(self):
        """
        Calculate the loss rate of the trades.

        Returns:
            float: The loss rate as a percentage.
        """
        if self.trade.empty:
            return 0.0

        loss_trades = self.trade[self.trade['cover_price'] < self.trade['order_price']]
        total_trades = self.total_trade_times()

        if total_trades == 0:
            return 0.0

        return len(loss_trades) / total_trades * 100
    
    def cal_win_loss_ratio(self):
        """
        Calculate the win-loss ratio of the trades.

        Returns:
            float: The win-loss ratio.
        """
        if self.trade.empty:
            return 0.0

        win_trades = self.trade[self.trade['cover_price'] > self.trade['order_price']]
        loss_trades = self.trade[self.trade['cover_price'] < self.trade['order_price']]

        if len(loss_trades) == 0:
            return float('inf')

        return len(win_trades) / len(loss_trades)
