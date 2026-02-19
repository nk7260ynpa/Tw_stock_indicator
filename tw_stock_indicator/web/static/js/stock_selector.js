/**
 * 股票選擇與日期區間互動邏輯。
 *
 * 提供股票搜尋、選擇、日期範圍設定、資料載入等功能。
 */

(function () {
    'use strict';

    var searchInput = document.getElementById('stock-search-input');
    var dropdown = document.getElementById('search-dropdown');
    var selectedStockEl = document.getElementById('selected-stock');
    var dateStart = document.getElementById('date-start');
    var dateEnd = document.getElementById('date-end');
    var queryBtn = document.getElementById('btn-query-stock');
    var loadStatus = document.getElementById('stock-load-status');

    var debounceTimer = null;
    var currentStock = null;

    /** 將已選股票資訊存在全域 */
    window.currentStockData = null;
    window.currentStock = null;

    /** Debounce 搜尋 */
    searchInput.addEventListener('input', function () {
        var keyword = searchInput.value.trim();
        if (debounceTimer) clearTimeout(debounceTimer);

        if (!keyword) {
            hideDropdown();
            return;
        }

        debounceTimer = setTimeout(function () {
            searchStocks(keyword);
        }, 300);
    });

    /** 點擊外部關閉下拉 */
    document.addEventListener('click', function (e) {
        if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
            hideDropdown();
        }
    });

    /** 搜尋股票 API */
    function searchStocks(keyword) {
        fetch('/api/stocks/search?q=' + encodeURIComponent(keyword))
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.error) {
                    showDropdownError(data.error);
                    return;
                }
                renderDropdown(data);
            })
            .catch(function () {
                showDropdownError('搜尋失敗');
            });
    }

    /** 渲染搜尋結果下拉 */
    function renderDropdown(stocks) {
        if (!stocks.length) {
            dropdown.innerHTML = '<div class="dropdown-empty">無符合結果</div>';
            dropdown.classList.add('show');
            return;
        }

        var html = '';
        stocks.forEach(function (stock) {
            html += '<div class="dropdown-item" '
                + 'data-code="' + stock.code + '" '
                + 'data-name="' + stock.name + '" '
                + 'data-market="' + stock.market + '">'
                + '<span class="dropdown-code">' + stock.code + '</span>'
                + '<span class="dropdown-name">' + stock.name + '</span>'
                + '<span class="dropdown-market">' + stock.market + '</span>'
                + '</div>';
        });
        dropdown.innerHTML = html;
        dropdown.classList.add('show');

        // 綁定點擊事件
        dropdown.querySelectorAll('.dropdown-item').forEach(function (item) {
            item.addEventListener('click', function () {
                selectStock(
                    item.dataset.code,
                    item.dataset.name,
                    item.dataset.market
                );
            });
        });
    }

    /** 顯示下拉錯誤 */
    function showDropdownError(msg) {
        dropdown.innerHTML = '<div class="dropdown-empty">' + msg + '</div>';
        dropdown.classList.add('show');
    }

    /** 隱藏下拉 */
    function hideDropdown() {
        dropdown.classList.remove('show');
    }

    /** 選擇股票 */
    function selectStock(code, name, market) {
        currentStock = { code: code, name: name, market: market };
        window.currentStock = currentStock;

        // 更新顯示
        selectedStockEl.innerHTML =
            '<span class="stock-badge">'
            + '<span class="badge-market">' + market + '</span>'
            + code + ' ' + name
            + '</span>';

        searchInput.value = '';
        hideDropdown();

        // 取得日期範圍
        fetchDateRange(market, code);
    }

    /** 取得日期範圍 */
    function fetchDateRange(market, code) {
        dateStart.disabled = true;
        dateEnd.disabled = true;
        queryBtn.disabled = true;

        fetch('/api/stocks/' + market + '/' + code + '/date-range')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.error || !data.min_date) {
                    showLoadStatus('無可用的日期資料', 'error');
                    return;
                }

                dateStart.min = data.min_date;
                dateStart.max = data.max_date;
                dateEnd.min = data.min_date;
                dateEnd.max = data.max_date;

                // 預設結束日為最新日期，起始日為最新日期往前 3 個月
                dateEnd.value = data.max_date;
                var startDefault = new Date(data.max_date);
                startDefault.setMonth(startDefault.getMonth() - 3);
                var startStr = startDefault.toISOString().slice(0, 10);
                dateStart.value = startStr < data.min_date ? data.min_date : startStr;

                dateStart.disabled = false;
                dateEnd.disabled = false;
                queryBtn.disabled = false;

                showLoadStatus(
                    '可查詢區間：' + data.min_date + ' ~ ' + data.max_date,
                    'info'
                );
            })
            .catch(function () {
                showLoadStatus('取得日期範圍失敗', 'error');
            });
    }

    /** 查詢按鈕點擊 */
    queryBtn.addEventListener('click', function () {
        if (!currentStock) return;

        var start = dateStart.value;
        var end = dateEnd.value;
        if (!start || !end) {
            showLoadStatus('請選擇起始與結束日期', 'error');
            return;
        }

        queryBtn.disabled = true;
        showLoadStatus('載入中...', 'info');

        var url = '/api/stocks/' + currentStock.market + '/'
            + currentStock.code + '/daily?start=' + start + '&end=' + end;

        fetch(url)
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.error) {
                    showLoadStatus(data.error, 'error');
                    queryBtn.disabled = false;
                    return;
                }

                window.currentStockData = data;
                showLoadStatus(
                    '已載入 ' + data.length + ' 筆日線資料'
                    + '（' + currentStock.code + ' ' + currentStock.name
                    + '，' + start + ' ~ ' + end + '）',
                    'success'
                );
                queryBtn.disabled = false;
            })
            .catch(function () {
                showLoadStatus('載入股價資料失敗', 'error');
                queryBtn.disabled = false;
            });
    });

    /** 顯示載入狀態 */
    function showLoadStatus(msg, type) {
        loadStatus.textContent = msg;
        loadStatus.className = 'stock-load-status';
        if (type) {
            loadStatus.classList.add('status-' + type);
        }
    }
})();
