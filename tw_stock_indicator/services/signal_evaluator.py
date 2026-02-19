"""訊號評估模組。

根據 RuleGroup 條件判斷進出場訊號。
"""

from tw_stock_indicator.models.rules import (
    Condition,
    LogicOperator,
    Operator,
    RuleGroup,
)


def _eval_condition(
    cond: Condition,
    series: dict[str, list[float | None]],
    idx: int,
) -> bool:
    """評估單一條件是否成立。

    Args:
        cond: 條件物件。
        series: 指標序列字典。
        idx: 當前 K 棒索引。

    Returns:
        條件是否成立。暖機期不足或資料不存在時回傳 False。
    """
    left_series = series.get(cond.left_param)
    right_series = series.get(cond.right_param)

    if left_series is None or right_series is None:
        return False

    left_val = left_series[idx] if idx < len(left_series) else None
    right_val = right_series[idx] if idx < len(right_series) else None

    if left_val is None or right_val is None:
        return False

    op = cond.operator

    if op == Operator.CROSS_ABOVE or op == Operator.CROSS_BELOW:
        # 穿越需要前一根 K 棒
        if idx < 1:
            return False

        prev_left = left_series[idx - 1] if (idx - 1) < len(left_series) else None
        prev_right = right_series[idx - 1] if (idx - 1) < len(right_series) else None

        if prev_left is None or prev_right is None:
            return False

        if op == Operator.CROSS_ABOVE:
            # 上穿：前一根 left <= right，當根 left > right
            return prev_left <= prev_right and left_val > right_val

        # 下穿：前一根 left >= right，當根 left < right
        return prev_left >= prev_right and left_val < right_val

    if op == Operator.GT:
        return left_val > right_val
    if op == Operator.GTE:
        return left_val >= right_val
    if op == Operator.LT:
        return left_val < right_val
    if op == Operator.LTE:
        return left_val <= right_val

    return False


def _eval_rule_group(
    group: RuleGroup,
    series: dict[str, list[float | None]],
    idx: int,
) -> bool:
    """評估規則群組是否成立。

    按 logic_operators 依序組合條件結果。

    Args:
        group: 規則群組。
        series: 指標序列字典。
        idx: 當前 K 棒索引。

    Returns:
        規則群組是否成立。
    """
    if not group.conditions:
        return False

    result = _eval_condition(group.conditions[0], series, idx)

    for i, cond in enumerate(group.conditions[1:], start=0):
        cond_result = _eval_condition(cond, series, idx)
        logic_op = (
            group.logic_operators[i]
            if i < len(group.logic_operators)
            else LogicOperator.AND
        )

        if logic_op == LogicOperator.AND:
            result = result and cond_result
        else:
            result = result or cond_result

    return result


def generate_signals(
    rule_groups: list[RuleGroup],
    series: dict[str, list[float | None]],
    n: int,
) -> dict[str, list[bool]]:
    """產出進出場訊號。

    同類型多群組間為 OR 關係（任一觸發即可）。

    Args:
        rule_groups: 規則群組列表。
        series: 指標序列字典。
        n: K 棒總數。

    Returns:
        包含 entry_signals 和 exit_signals 的字典，各為長度 n 的布林列表。
    """
    entry_groups = [g for g in rule_groups if g.rule_type == "entry"]
    exit_groups = [g for g in rule_groups if g.rule_type == "exit"]

    entry_signals = [False] * n
    exit_signals = [False] * n

    for i in range(n):
        # 進場：任一進場群組成立即觸發
        for group in entry_groups:
            if _eval_rule_group(group, series, i):
                entry_signals[i] = True
                break

        # 出場：任一出場群組成立即觸發
        for group in exit_groups:
            if _eval_rule_group(group, series, i):
                exit_signals[i] = True
                break

    return {"entry_signals": entry_signals, "exit_signals": exit_signals}
