/**
 * 規則設計器互動邏輯。
 *
 * 提供展開/收合、動態載入參數、新增/刪除條件等功能。
 */

/** 切換規則群組展開/收合 */
function toggleGroup(header) {
    var group = header.closest('.rule-group');
    group.classList.toggle('collapsed');
}

/** 指標類型變更時動態載入參數 */
function onIndicatorTypeChange(selectEl) {
    var form = selectEl.closest('.add-condition-form');
    var leftSelect = form.querySelector('.select-left-param');
    var rightSelect = form.querySelector('.select-right-param');
    var indicatorType = selectEl.value;

    leftSelect.innerHTML = '<option value="">左側參數</option>';
    rightSelect.innerHTML = '<option value="">右側參數</option>';

    if (!indicatorType) return;

    fetch('/api/indicators/' + encodeURIComponent(indicatorType) + '/params')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            data.params.forEach(function (p) {
                leftSelect.innerHTML += '<option value="' + p + '">' + p + '</option>';
                rightSelect.innerHTML += '<option value="' + p + '">' + p + '</option>';
            });
        });
}

/** 新增條件至規則群組 */
function addCondition(groupId) {
    var form = document.querySelector('.add-condition-form[data-group-id="' + groupId + '"]');
    var indicatorType = form.querySelector('.select-indicator-type').value;
    var leftParam = form.querySelector('.select-left-param').value;
    var operator = form.querySelector('.select-operator').value;
    var rightParam = form.querySelector('.select-right-param').value;
    var logicOp = form.querySelector('.select-logic-op').value;

    if (!indicatorType || !leftParam || !operator || !rightParam) {
        return;
    }

    fetch('/api/rules/' + groupId + '/conditions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            indicator_type: indicatorType,
            left_param: leftParam,
            operator: operator,
            right_param: rightParam,
            logic_operator: logicOp
        })
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
        if (data.error) return;

        var list = form.closest('.rule-group-body').querySelector('.conditions-list');
        var hasConditions = list.querySelectorAll('.condition-row').length > 0;

        var row = document.createElement('div');
        row.className = 'condition-row';
        row.dataset.conditionId = data.id;

        var html = '';
        if (hasConditions) {
            html += '<span class="logic-op">' + logicOp + '</span>';
        }
        html += '<span class="condition-text">';
        html += data.indicator_type + ': ';
        html += data.left_param + ' ' + data.operator + ' ' + data.right_param;
        html += '</span>';
        html += '<button class="btn btn-sm btn-delete" onclick="deleteCondition(\'' + groupId + '\', \'' + data.id + '\')">&#10005;</button>';

        row.innerHTML = html;
        list.appendChild(row);
    });
}

/** 刪除條件 */
function deleteCondition(groupId, conditionId) {
    fetch('/api/rules/' + groupId + '/conditions/' + conditionId, {
        method: 'DELETE'
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
        if (data.error) return;
        var row = document.querySelector('.condition-row[data-condition-id="' + conditionId + '"]');
        if (row) row.remove();
    });
}

/** 新增規則群組 */
function createRuleGroup(ruleType) {
    var name = prompt(ruleType === 'entry' ? '請輸入進場規則名稱：' : '請輸入出場規則名稱：');
    if (!name) return;

    fetch('/api/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, rule_type: ruleType })
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
        if (data.error) return;
        location.reload();
    });
}

/** 初始化事件監聽 */
document.addEventListener('DOMContentLoaded', function () {
    // 指標類型下拉選單變更事件
    document.querySelectorAll('.select-indicator-type').forEach(function (sel) {
        sel.addEventListener('change', function () { onIndicatorTypeChange(this); });
    });

    // 新增進場/出場規則按鈕
    var entryBtn = document.getElementById('btn-add-entry-rule');
    if (entryBtn) {
        entryBtn.addEventListener('click', function () { createRuleGroup('entry'); });
    }

    var exitBtn = document.getElementById('btn-add-exit-rule');
    if (exitBtn) {
        exitBtn.addEventListener('click', function () { createRuleGroup('exit'); });
    }
});
