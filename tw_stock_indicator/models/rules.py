"""規則資料模型。

定義進出場規則的資料結構，包含指標類型、運算子、條件與規則群組。
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum


class IndicatorType(str, Enum):
    """技術指標類型。"""

    MA = "MA"
    RSI = "RSI"
    MACD = "MACD"
    KD = "KD"
    BOLLINGER = "BOLLINGER"


class Operator(str, Enum):
    """比較運算子。"""

    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    CROSS_ABOVE = "上穿"
    CROSS_BELOW = "下穿"


class LogicOperator(str, Enum):
    """邏輯運算子。"""

    AND = "AND"
    OR = "OR"


@dataclass
class Condition:
    """單一條件。

    Attributes:
        indicator_type: 技術指標類型。
        left_param: 左側參數（如 MA5）。
        operator: 比較運算子。
        right_param: 右側參數（如 MA20）。
        id: 條件唯一識別碼。
    """

    indicator_type: IndicatorType
    left_param: str
    operator: Operator
    right_param: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


@dataclass
class RuleGroup:
    """規則群組。

    Attributes:
        name: 群組名稱。
        rule_type: 規則類型（entry 進場 / exit 出場）。
        conditions: 條件列表。
        logic_operators: 條件間的邏輯運算子列表。
        id: 群組唯一識別碼。
    """

    name: str
    rule_type: str
    conditions: list[Condition] = field(default_factory=list)
    logic_operators: list[LogicOperator] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
