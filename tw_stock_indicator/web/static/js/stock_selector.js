/**
 * 股票選擇與日期區間互動邏輯。
 *
 * 提供股票搜尋、選擇、日期範圍設定、資料載入、回測計算等功能。
 */

(function () {
    'use strict';

    var searchInput = document.getElementById('stock-search-input');
    var dropdown = document.getElementById('search-dropdown');
    var dateStart = document.getElementById('date-start');
    var dateEnd = document.getElementById('date-end');
    var sharesInput = document.getElementById('stock-shares');
    var queryBtn = document.getElementById('btn-query-stock');
    var loadStatus = document.getElementById('stock-load-status');

    var debounceTimer = null;
    var currentStock = null;

    /** 將已選股票資訊存在全域 */
    window.currentStockData = null;
    window.currentStock = null;
    window.currentShares = 1000;

    /** 點擊搜尋欄位時清空以便重新搜尋 */
    searchInput.addEventListener('focus', function () {
        searchInput.select();
    });

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

        // 將選中的股票顯示在搜尋欄位
        searchInput.value = code + ' ' + name + ' (' + market + ')';
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

    /** 計算按鈕點擊：載入日線 → 呼叫回測 API → 更新指標 */
    queryBtn.addEventListener('click', function () {
        if (!currentStock) return;

        var start = dateStart.value;
        var end = dateEnd.value;
        if (!start || !end) {
            showLoadStatus('請選擇起始與結束日期', 'error');
            return;
        }

        window.currentShares = parseInt(sharesInput.value, 10) || 1000;
        queryBtn.disabled = true;
        queryBtn.classList.add('btn-calculating');
        queryBtn.textContent = '計算中...';
        showLoadStatus('載入日線資料中...', 'info');

        var url = '/api/stocks/' + currentStock.market + '/'
            + currentStock.code + '/daily?start=' + start + '&end=' + end;

        fetch(url)
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.error) {
                    showLoadStatus(data.error, 'error');
                    resetBtn();
                    return;
                }

                window.currentStockData = data;
                showLoadStatus(
                    '已載入 ' + data.length + ' 筆日線資料，正在執行回測...',
                    'info'
                );

                // 呼叫回測 API
                return runBacktest(data, window.currentShares);
            })
            .then(function (result) {
                if (!result) return;

                // 更新指標卡片
                updateIndicatorCards(result.indicators);

                // 先顯示區塊（讓容器有寬高），再渲染圖表
                showChartSection();
                showIndicatorSection();

                if (window.StockChart) {
                    window.StockChart.render(
                        window.currentStockData,
                        result.trades,
                        result.indicator_series
                    );
                }

                showLoadStatus(
                    '回測完成（' + currentStock.code + ' ' + currentStock.name
                    + '，' + start + ' ~ ' + end
                    + '，' + window.currentShares + ' 股）',
                    'success'
                );
                resetBtn();
            })
            .catch(function () {
                showLoadStatus('回測計算失敗', 'error');
                resetBtn();
            });
    });

    /** 呼叫回測 API */
    function runBacktest(dailyData, shares) {
        return fetch('/api/backtest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                daily_data: dailyData,
                shares: shares
            })
        })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.error) {
                showLoadStatus(data.error, 'error');
                resetBtn();
                return null;
            }
            return data;
        });
    }

    /** 更新指標卡片 DOM */
    function updateIndicatorCards(indicators) {
        var grid = document.getElementById('indicator-grid');
        if (!grid) return;

        // 清空現有卡片並重建
        var html = '';
        indicators.forEach(function (ind) {
            var valueClass = 'indicator-value';
            if (ind.value === null) {
                // None → "--"，不加顏色
            } else if (ind.value < 0) {
                valueClass += ' negative';
            } else {
                valueClass += ' positive';
            }

            html += '<div class="indicator-card" data-code="' + ind.code + '">'
                + '<div class="indicator-name">' + ind.name + '</div>'
                + '<div class="' + valueClass + '">' + ind.formatted_value + '</div>'
                + '<div class="indicator-desc">' + ind.description + '</div>'
                + '</div>';
        });
        grid.innerHTML = html;
    }

    /** 顯示圖表區塊 + 動畫 + 滾動 */
    function showChartSection() {
        var section = document.getElementById('chart-section');
        if (!section) return;

        section.style.display = '';
        section.classList.remove('fade-in');
        void section.offsetWidth;
        section.classList.add('fade-in');

        // 更新圖表資訊
        var meta = document.getElementById('chart-meta');
        if (meta && currentStock) {
            meta.textContent = '（' + currentStock.code + ' '
                + currentStock.name + '，' + window.currentShares + ' 股）';
        }

        // 自動滾動到圖表區塊
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    /** 顯示績效指標區塊 + 動畫 */
    function showIndicatorSection() {
        var section = document.getElementById('indicator-section');
        if (!section) return;

        section.style.display = '';
        section.classList.remove('fade-in');
        void section.offsetWidth;
        section.classList.add('fade-in');

        // 更新回測資訊
        var meta = document.getElementById('backtest-meta');
        if (meta && currentStock) {
            meta.textContent = '（' + currentStock.code + ' '
                + currentStock.name + '，' + window.currentShares + ' 股）';
        }
    }

    /** 重設按鈕狀態 */
    function resetBtn() {
        queryBtn.disabled = false;
        queryBtn.classList.remove('btn-calculating');
        queryBtn.textContent = '計算';
    }

    /** 顯示載入狀態 */
    function showLoadStatus(msg, type) {
        loadStatus.textContent = msg;
        loadStatus.className = 'stock-load-status';
        if (type) {
            loadStatus.classList.add('status-' + type);
        }
    }
})();
