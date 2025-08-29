from routers import MyTWSESQLRouter
from strategy import MAExceedStrategy

HOST = "localhost:3306"
USER = "root"
PASSWORD = "stock"

router = MyTWSESQLRouter(HOST, USER, PASSWORD)

start_date = "2025-01-01"
end_date = "2025-06-30"
security_code = "2330"

data = router.load_data(start_date, end_date, security_code)

calculator = MAExceedStrategy()
trade = calculator(data)
print(trade)