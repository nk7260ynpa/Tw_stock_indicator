from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    """
    def __init__(self, name: str):
        self.name = name
        self.position = 0

    @abstractmethod
    def buy_condition(self) -> bool:
        pass

    @abstractmethod
    def sell_condition(self) -> bool:
        pass

    def buy_stock(self):
        self.position += 1
        print(f"{self.name} bought a stock. Current position: {self.position}")

    def sell_stock(self):
        self.postition = 0

    def __call__(self):
        if self.buy_condition():
            self.buy_stock()
        elif self.sell_condition():
            self.sell_stock()
        else:
            print(f"{self.name} is holding position. Current position: {self.position}")
