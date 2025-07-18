
class BaseStrategy:
    """
    Base class for all trading strategies.
    """
    def __init__(self, name: str):
        self.name = name
