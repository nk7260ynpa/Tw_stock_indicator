import pandas as pd

class StockIndicator:
    def __init__(self, code, stock_type='stock'):
        self.code = code
        self.stock_type = stock_type
        self.total_profit = 0.0
        self.total
