"""規則服務模組。

提供規則群組的 CRUD 操作與指標參數對照。
"""

from tw_stock_indicator.models.rules import (
    Condition,
    IndicatorType,
    LogicOperator,
    Operator,
    RuleGroup,
)

# 各指標可選參數對照
_INDICATOR_PARAMS: dict[IndicatorType, list[str]] = {
    IndicatorType.MA: ["MA5", "MA10", "MA20", "MA60", "MA120", "MA240", "收盤價"],
    IndicatorType.RSI: ["RSI6", "RSI12", "RSI24", "50", "70", "30", "80", "20"],
    IndicatorType.MACD: ["DIF", "MACD", "OSC", "0"],
    IndicatorType.KD: ["K", "D", "20", "50", "80"],
    IndicatorType.BOLLINGER: ["上軌", "中軌", "下軌", "收盤價"],
}

# 記憶體儲存
_rule_groups: dict[str, RuleGroup] = {}


def get_indicator_params(indicator_type: IndicatorType) -> list[str]:
    """取得指定指標類型的可選參數。

    Args:
        indicator_type: 技術指標類型。

    Returns:
        可選參數字串列表。
    """
    return _INDICATOR_PARAMS.get(indicator_type, [])


def create_rule_group(name: str, rule_type: str) -> RuleGroup:
    """建立新的規則群組。

    Args:
        name: 群組名稱。
        rule_type: 規則類型（entry / exit）。

    Returns:
        新建立的 RuleGroup 物件。
    """
    group = RuleGroup(name=name, rule_type=rule_type)
    _rule_groups[group.id] = group
    return group


def add_condition(
    group_id: str,
    indicator_type: IndicatorType,
    left_param: str,
    operator: Operator,
    right_param: str,
    logic_operator: LogicOperator = LogicOperator.AND,
) -> Condition | None:
    """新增條件至規則群組。

    Args:
        group_id: 規則群組 ID。
        indicator_type: 技術指標類型。
        left_param: 左側參數。
        operator: 比較運算子。
        right_param: 右側參數。
        logic_operator: 與前一條件的邏輯運算子，預設 AND。

    Returns:
        新建立的 Condition 物件，若群組不存在則回傳 None。
    """
    group = _rule_groups.get(group_id)
    if group is None:
        return None

    condition = Condition(
        indicator_type=indicator_type,
        left_param=left_param,
        operator=operator,
        right_param=right_param,
    )

    if group.conditions:
        group.logic_operators.append(logic_operator)

    group.conditions.append(condition)
    return condition


def remove_condition(group_id: str, condition_id: str) -> bool:
    """從規則群組移除條件。

    Args:
        group_id: 規則群組 ID。
        condition_id: 條件 ID。

    Returns:
        移除成功回傳 True，否則 False。
    """
    group = _rule_groups.get(group_id)
    if group is None:
        return False

    for i, cond in enumerate(group.conditions):
        if cond.id == condition_id:
            group.conditions.pop(i)
            # 移除對應的邏輯運算子
            if group.logic_operators:
                idx = min(i, len(group.logic_operators) - 1)
                if i > 0:
                    idx = i - 1
                group.logic_operators.pop(idx)
            return True

    return False


def get_all_rule_groups() -> list[RuleGroup]:
    """取得所有規則群組。

    Returns:
        所有 RuleGroup 物件的列表。
    """
    return list(_rule_groups.values())


def get_rule_group(group_id: str) -> RuleGroup | None:
    """取得指定規則群組。

    Args:
        group_id: 規則群組 ID。

    Returns:
        RuleGroup 物件，若不存在則回傳 None。
    """
    return _rule_groups.get(group_id)


def reset_store() -> None:
    """清空記憶體儲存（供測試使用）。"""
    _rule_groups.clear()


def load_default_rules() -> None:
    """載入預設進出場規則群組。"""
    # 進場規則：MA 黃金交叉 + RSI 未過熱
    entry = create_rule_group("均線黃金交叉進場", "entry")
    add_condition(
        entry.id, IndicatorType.MA, "MA5", Operator.CROSS_ABOVE, "MA20"
    )
    add_condition(
        entry.id, IndicatorType.RSI, "RSI12", Operator.LT, "70",
        LogicOperator.AND,
    )

    # 出場規則：MA 死亡交叉
    exit_group = create_rule_group("均線死亡交叉出場", "exit")
    add_condition(
        exit_group.id, IndicatorType.MA, "MA5", Operator.CROSS_BELOW, "MA20"
    )
