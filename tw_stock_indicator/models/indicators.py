"""指標資料模型。

定義技術指標的資料結構與格式化方法。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Indicator:
    """股市技術指標。

    Attributes:
        code: 指標代碼（如 win_rate）。
        name: 指標名稱（如「勝率」）。
        value: 指標數值。
        unit: 單位（如 %、倍、元、次）。
        description: 指標說明。
    """

    code: str
    name: str
    value: float
    unit: str
    description: str

    def formatted_value(self) -> str:
        """回傳帶單位的格式化數值字串。

        Returns:
            格式化後的字串，例如 '62.5%'、'1.85 倍'。
        """
        if self.unit == "%":
            return f"{self.value}%"
        if self.unit in ("倍", "次"):
            return f"{self.value:,.0f} {self.unit}" if self.value == int(self.value) else f"{self.value} {self.unit}"
        if self.unit == "元":
            return f"{self.value:,.0f} {self.unit}" if self.value == int(self.value) else f"{self.value:,.2f} {self.unit}"
        return f"{self.value} {self.unit}"
