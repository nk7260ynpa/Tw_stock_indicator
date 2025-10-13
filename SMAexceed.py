import argparse

import mplfinance as mpf

from routers import MyTWSESQLRouter
from strategy import SMAExceedStrategy
from indicator import StockIndicator
from utils import ChartTrade

def main(opt):
    HOST = opt.host
    USER = opt.user
    PASSWORD = opt.password

    router = MyTWSESQLRouter(HOST, USER, PASSWORD)

    start_date = opt.start_date
    end_date = opt.end_date
    security_code = opt.security_code

    data = router.load_data(start_date, end_date, security_code)

    calculator = SMAExceedStrategy()
    trade = calculator(data)
    indicator = StockIndicator(trade, start_date, end_date, stock_type='Stock')
    indicator.show()
    addp = [mpf.make_addplot(data['SMA1']), 
            mpf.make_addplot(data['SMA2']), 
            mpf.make_addplot(data['SMA3'])]
    ChartTrade(data, trade, addp=addp, v_enable=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost:3306", help="Database host")
    parser.add_argument("--user", type=str, default="root", help="Database user")
    parser.add_argument("--password", type=str, default="stock", help="Database password")
    parser.add_argument("--start_date", type=str, default="2025-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, default="2025-06-30", help="End date (YYYY-MM-DD)")
    parser.add_argument("--security_code", type=str, default="2330", help="Security code")
    opt = parser.parse_args()
    main(opt)
    