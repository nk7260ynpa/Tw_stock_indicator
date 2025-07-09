import pandas as pd

from routers import MyTWSESQLRouter

HOST = "localhost:3306"
USER = "root"
PASSWORD = "stock"
DBNAME = "TWSE"

Router = MyTWSESQLRouter(HOST, USER, PASSWORD, DBNAME)
data = Router.get_data("2025-01-01", "2025-06-31", "2330")

