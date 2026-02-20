/**
 * K 線圖渲染模組。
 *
 * 使用 TradingView Lightweight Charts v4 繪製主圖（K 線 + 成交量 + 指標疊加）
 * 與子圖（RSI、KD、MACD）。暴露 window.StockChart.render / destroy。
 */

(function () {
    'use strict';

    /** 指標線顏色對照 */
    var LINE_COLORS = {
        MA5: '#f0b90b',
        MA10: '#e491ff',
        MA20: '#58a6ff',
        MA60: '#3fb950',
        MA120: '#f85149',
        MA240: '#ff7b72',
        '上軌': '#8b949e',
        '中軌': '#58a6ff',
        '下軌': '#8b949e',
        RSI6: '#f0b90b',
        RSI12: '#58a6ff',
        RSI24: '#e491ff',
        K: '#f0b90b',
        D: '#58a6ff',
        DIF: '#58a6ff',
        MACD: '#f0b90b',
        OSC: '#3fb950',
    };

    /** 深色主題共用設定 */
    var DARK_THEME = {
        layout: {
            background: { color: '#161b22' },
            textColor: '#8b949e',
        },
        grid: {
            vertLines: { color: '#21262d' },
            horzLines: { color: '#21262d' },
        },
        crosshair: {
            mode: 0,
        },
        timeScale: {
            borderColor: '#30363d',
            timeVisible: false,
        },
        rightPriceScale: {
            borderColor: '#30363d',
        },
    };

    /** 主圖子圖實例暫存 */
    var charts = [];
    var resizeObservers = [];

    /** 建立圖表並掛載 ResizeObserver */
    function createChart(container, opts) {
        var merged = Object.assign({}, DARK_THEME, opts || {}, {
            width: container.clientWidth,
            height: container.clientHeight,
        });
        var chart = LightweightCharts.createChart(container, merged);

        var ro = new ResizeObserver(function (entries) {
            for (var i = 0; i < entries.length; i++) {
                var cr = entries[i].contentRect;
                chart.applyOptions({ width: cr.width });
            }
        });
        ro.observe(container);
        resizeObservers.push(ro);
        charts.push(chart);
        return chart;
    }

    /**
     * 判斷指標 key 的繪製位置。
     *
     * @param {string} key - 指標 key
     * @returns {string} 'main' | 'rsi' | 'kd' | 'macd'
     */
    function classifyIndicator(key) {
        if (/^MA\d+$/.test(key) || key === '上軌' || key === '中軌' || key === '下軌') {
            return 'main';
        }
        if (/^RSI\d+$/.test(key)) return 'rsi';
        if (key === 'K' || key === 'D') return 'kd';
        if (key === 'DIF' || key === 'MACD' || key === 'OSC') return 'macd';
        return 'main';
    }

    /**
     * 將日線 date（YYYY-MM-DD）轉為 Lightweight Charts 可用的時間格式。
     */
    function toChartTime(dateStr) {
        return dateStr;
    }

    /** 渲染主圖（K 線 + 成交量 + 標記 + 指標疊加） */
    function renderMainChart(container, dailyData, trades, mainSeries) {
        var chart = createChart(container, {
            localization: {
                priceFormatter: function (price) {
                    return price.toFixed(2);
                },
            },
        });

        // K 線（台股：綠漲紅跌）
        var candleSeries = chart.addCandlestickSeries({
            upColor: '#3fb950',
            downColor: '#f85149',
            borderUpColor: '#3fb950',
            borderDownColor: '#f85149',
            wickUpColor: '#3fb950',
            wickDownColor: '#f85149',
        });

        var candleData = dailyData.map(function (d) {
            return {
                time: toChartTime(d.date),
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close,
            };
        });
        candleSeries.setData(candleData);

        // 成交量（獨立 priceScale，佔底部 20%）
        var volumeSeries = chart.addHistogramSeries({
            priceFormat: { type: 'volume' },
            priceScaleId: 'volume',
        });
        chart.priceScale('volume').applyOptions({
            scaleMargins: { top: 0.8, bottom: 0 },
        });

        var volumeData = dailyData.map(function (d) {
            return {
                time: toChartTime(d.date),
                value: d.volume,
                color: d.close >= d.open
                    ? 'rgba(63, 185, 80, 0.3)'
                    : 'rgba(248, 81, 73, 0.3)',
            };
        });
        volumeSeries.setData(volumeData);

        // 進出場標記
        if (trades && trades.length > 0) {
            var markers = [];
            trades.forEach(function (t) {
                markers.push({
                    time: toChartTime(t.entry_date),
                    position: 'belowBar',
                    color: '#3fb950',
                    shape: 'arrowUp',
                    text: 'B ' + t.entry_price.toFixed(1),
                });
                var pnlText = t.pnl >= 0
                    ? '+' + t.pnl.toFixed(0)
                    : t.pnl.toFixed(0);
                markers.push({
                    time: toChartTime(t.exit_date),
                    position: 'aboveBar',
                    color: '#f85149',
                    shape: 'arrowDown',
                    text: 'S ' + t.exit_price.toFixed(1) + ' (' + pnlText + ')',
                });
            });
            // 標記需要依時間排序
            markers.sort(function (a, b) {
                return a.time < b.time ? -1 : a.time > b.time ? 1 : 0;
            });
            candleSeries.setMarkers(markers);
        }

        // 主圖疊加指標線
        var keys = Object.keys(mainSeries);
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            var isBollBand = (key === '上軌' || key === '下軌');
            var lineStyle = isBollBand
                ? LightweightCharts.LineStyle.Dashed
                : LightweightCharts.LineStyle.Solid;

            var lineSeries = chart.addLineSeries({
                color: LINE_COLORS[key] || '#8b949e',
                lineWidth: isBollBand ? 1 : 2,
                lineStyle: lineStyle,
                priceLineVisible: false,
                lastValueVisible: false,
                crosshairMarkerVisible: false,
            });

            var lineData = [];
            var seriesValues = mainSeries[key];
            for (var j = 0; j < dailyData.length; j++) {
                if (seriesValues[j] !== null && seriesValues[j] !== undefined) {
                    lineData.push({
                        time: toChartTime(dailyData[j].date),
                        value: seriesValues[j],
                    });
                }
            }
            lineSeries.setData(lineData);
        }

        chart.timeScale().fitContent();
        return chart;
    }

    /** 建立子圖 DOM 容器 */
    function createSubChartDiv(parentContainer, label) {
        var wrapper = document.createElement('div');
        wrapper.className = 'chart-sub-wrapper';

        var labelEl = document.createElement('div');
        labelEl.className = 'chart-sub-label';
        labelEl.textContent = label;
        wrapper.appendChild(labelEl);

        var chartDiv = document.createElement('div');
        chartDiv.className = 'chart-sub';
        wrapper.appendChild(chartDiv);

        parentContainer.appendChild(wrapper);
        return chartDiv;
    }

    /** 渲染子圖（RSI / KD / MACD） */
    function renderSubChart(container, dailyData, seriesGroup, type) {
        var chart = createChart(container);
        var keys = Object.keys(seriesGroup);

        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            var values = seriesGroup[key];

            // OSC 使用柱狀圖
            if (key === 'OSC') {
                var histSeries = chart.addHistogramSeries({
                    priceLineVisible: false,
                    lastValueVisible: false,
                });
                var histData = [];
                for (var j = 0; j < dailyData.length; j++) {
                    if (values[j] !== null && values[j] !== undefined) {
                        histData.push({
                            time: toChartTime(dailyData[j].date),
                            value: values[j],
                            color: values[j] >= 0
                                ? 'rgba(63, 185, 80, 0.6)'
                                : 'rgba(248, 81, 73, 0.6)',
                        });
                    }
                }
                histSeries.setData(histData);
            } else {
                var lineSeries = chart.addLineSeries({
                    color: LINE_COLORS[key] || '#8b949e',
                    lineWidth: 2,
                    priceLineVisible: false,
                    lastValueVisible: false,
                    crosshairMarkerVisible: false,
                });
                var lineData = [];
                for (var j = 0; j < dailyData.length; j++) {
                    if (values[j] !== null && values[j] !== undefined) {
                        lineData.push({
                            time: toChartTime(dailyData[j].date),
                            value: values[j],
                        });
                    }
                }
                lineSeries.setData(lineData);
            }
        }

        chart.timeScale().fitContent();
        return chart;
    }

    /** 銷毀所有圖表實例 */
    function destroy() {
        for (var i = 0; i < resizeObservers.length; i++) {
            resizeObservers[i].disconnect();
        }
        resizeObservers = [];

        for (var i = 0; i < charts.length; i++) {
            charts[i].remove();
        }
        charts = [];

        // 清空子圖容器
        var subContainer = document.getElementById('sub-charts-container');
        if (subContainer) {
            subContainer.innerHTML = '';
        }
    }

    /**
     * 渲染完整圖表（主圖 + 子圖）。
     *
     * @param {Array} dailyData - 日線資料
     * @param {Array} trades - 交易紀錄
     * @param {Object} indicatorSeries - 技術指標序列
     */
    function render(dailyData, trades, indicatorSeries) {
        destroy();

        if (!dailyData || dailyData.length === 0) return;

        // 分類指標
        var mainSeries = {};
        var rsiSeries = {};
        var kdSeries = {};
        var macdSeries = {};

        var seriesKeys = Object.keys(indicatorSeries || {});
        for (var i = 0; i < seriesKeys.length; i++) {
            var key = seriesKeys[i];
            var target = classifyIndicator(key);
            if (target === 'main') mainSeries[key] = indicatorSeries[key];
            else if (target === 'rsi') rsiSeries[key] = indicatorSeries[key];
            else if (target === 'kd') kdSeries[key] = indicatorSeries[key];
            else if (target === 'macd') macdSeries[key] = indicatorSeries[key];
        }

        // 主圖
        var mainContainer = document.getElementById('main-chart');
        if (mainContainer) {
            renderMainChart(mainContainer, dailyData, trades, mainSeries);
        }

        // 子圖
        var subContainer = document.getElementById('sub-charts-container');
        if (!subContainer) return;

        if (Object.keys(rsiSeries).length > 0) {
            var rsiDiv = createSubChartDiv(subContainer, 'RSI');
            renderSubChart(rsiDiv, dailyData, rsiSeries, 'rsi');
        }
        if (Object.keys(kdSeries).length > 0) {
            var kdDiv = createSubChartDiv(subContainer, 'KD');
            renderSubChart(kdDiv, dailyData, kdSeries, 'kd');
        }
        if (Object.keys(macdSeries).length > 0) {
            var macdDiv = createSubChartDiv(subContainer, 'MACD');
            renderSubChart(macdDiv, dailyData, macdSeries, 'macd');
        }
    }

    window.StockChart = {
        render: render,
        destroy: destroy,
    };
})();
