# Tw Stock Indicator

台灣股票技術指標分析工具，提供 Web 儀表板展示股市進出場盈利指標與規則設計器。
支援從自架 MySQL 資料庫查詢實際股票資料，可選擇股票代碼與日期區間。

## 專案架構

```
tw_stock_indicator/              # 主程式套件
    __init__.py                  # 套件初始化，定義版本號
    main.py                      # 程式進入點（支援 --web 啟動儀表板）
    logger.py                    # logging 配置模組
    models/                      # 資料模型
        __init__.py
        indicators.py            # 指標 dataclass
        rules.py                 # 規則 dataclass + Enum
    services/                    # 業務邏輯
        __init__.py
        indicator_service.py     # 示範指標資料
        indicator_calculator.py  # 技術指標計算（MA、RSI、MACD、KD、布林通道）
        signal_evaluator.py      # 訊號評估（根據規則判斷進出場訊號）
        backtest_service.py      # 回測服務（交易模擬 + 績效指標計算）
        rule_service.py          # 規則 CRUD（記憶體儲存）
        stock_service.py         # 股票資料查詢（MySQL）
    web/                         # Flask Web 層
        __init__.py              # App Factory
        routes/
            __init__.py
            dashboard.py         # 首頁路由（GET /）
            api.py               # 規則 API + 股票資料 API + 回測 API（RESTful）
        templates/               # Jinja2 模板
            base.html            # 深色主題基礎版型
            dashboard.html       # 儀表板頁面
            components/
                indicator_card.html   # 指標卡片元件
                rule_designer.html    # 規則設計器元件
                stock_selector.html   # 股票選擇與日期區間元件
        static/
            css/main.css         # 深色主題樣式
            js/dashboard.js      # 卡片互動
            js/chart.js          # K 線圖渲染（Lightweight Charts）
            js/stock_selector.js # 股票搜尋與日期互動
            js/rule_designer.js  # 規則設計器互動
tests/                           # 單元測試
    __init__.py
    test_main.py                 # main 模組測試
    test_models.py               # 資料模型測試
    test_services.py             # 服務層測試
    test_stock_service.py        # 股票服務測試（mock DB）
    test_backtest.py             # 回測引擎測試（指標計算、訊號評估、回測服務）
    test_web.py                  # Flask 路由與 API 測試（含回測 API）
docker/                          # Docker 相關
    Dockerfile                   # Python 3.12 base image
    build.sh                     # 建立 image 腳本
    docker-compose.yaml          # 啟動設定（連接 DB 網路）
logs/                            # log 輸出目錄
    .gitkeep
run.sh                           # 啟動 Web 儀表板腳本（docker compose）
requirements.txt                 # Python 依賴清單
```

## 前置需求

- Docker 與 Docker Compose
- MySQL 資料庫容器（`tw_stock_database`）已在 `db_network` 網路中運行
- 資料庫包含 `TWSE.StockName`、`TWSE.DailyPrice`、`TPEX.StockName`、`TPEX.DailyPrice` 資料表

## 使用方法

### 建立 Docker Image

```bash
bash docker/build.sh
```

### 啟動 Web 儀表板

```bash
bash run.sh
```

啟動後瀏覽器開啟 `http://localhost:5001` 即可檢視儀表板。
可透過環境變數自訂設定：

```bash
HOST_PORT=8080 DB_HOST=myhost DB_USER=myuser DB_PASSWORD=mypass bash run.sh
```

### 功能說明

- **股票選擇器**：搜尋股票代碼或名稱（支援上市 TWSE / 上櫃 TPEX），選擇後自動帶入可查詢日期範圍
- **日期區間選擇**：選定起始與結束日期後，載入該股票的日線資料
- **規則設計器**：可新增/刪除進出場規則群組與條件，支援多種技術指標（MA、RSI、MACD、KD、布林通道）
- **回測計算**：根據設定的進出場規則與日線資料執行回測，計算 8 項績效指標（勝率、獲利因子、期望值、最大回撤、夏普比率、獲利虧損比、年化報酬率、總交易次數）。損益計算包含券商手續費（0.1425%，最低 20 元）與證交稅（賣出 0.3%）
- **技術分析圖表**：回測完成後顯示 K 線圖（含成交量）、進出場標記（買/賣箭頭）、疊加規則使用中的技術指標線（MA、布林通道、RSI、KD、MACD），使用 TradingView Lightweight Charts v4
- **績效指標卡片**：回測完成後顯示計算結果（預設隱藏，點擊「計算」後顯示）

### API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/indicators/<type>/params` | 取得指標可選參數 |
| GET | `/api/rules` | 列出所有規則群組 |
| POST | `/api/rules` | 建立規則群組 |
| POST | `/api/rules/<id>/conditions` | 新增條件 |
| DELETE | `/api/rules/<id>/conditions/<cid>` | 刪除條件 |
| GET | `/api/stocks/search?q=<keyword>` | 搜尋股票（代碼或名稱） |
| GET | `/api/stocks/<market>/<code>/daily?start=<date>&end=<date>` | 取得日線資料 |
| GET | `/api/stocks/<market>/<code>/date-range` | 取得可查詢日期範圍 |
| POST | `/api/backtest` | 執行回測計算（需傳入 daily_data 與 shares） |

### 執行單元測試

先建立 Docker image，再於容器中執行測試：

```bash
docker run --rm tw-stock-indicator pytest tests/
```

## 授權

MIT License
