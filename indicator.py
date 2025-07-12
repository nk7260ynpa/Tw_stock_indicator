

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
        self.data = data
        self.stock_type = stock_type
        self.profit_rate = self._get_profit_rate()
        self.tax_rate = self._get_tax_rate()
        self.trade_times = self._get_trade_times()
        self.average_profit_rate = self._get_average_profit_rate()

    def _get_tax_rate(self):
        """
        Get the tax rate based on the stock type.

        Returns:
            float: The tax rate for the stock type.
        """
        if self.stock_type == 'stock':
            return 0.003 + 0.00285
        elif self.stock_type == 'etf':
            return 0.001 + 0.00285
        else:
            raise ValueError("Invalid stock type. Must be 'stock' or 'etf'.")
        
    def _get_profit_rate(self):
        return (self.trade["sell_price"] - self.trade["buy_price"]) / self.trade["buy_price"] - self.tax_rate

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

