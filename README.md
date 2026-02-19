# Tw Stock Indicator

台灣股票技術指標分析工具，提供 Web 儀表板展示股市進出場盈利指標與規則設計器。

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
        rule_service.py          # 規則 CRUD（記憶體儲存）
    web/                         # Flask Web 層
        __init__.py              # App Factory
        routes/
            __init__.py
            dashboard.py         # 首頁路由（GET /）
            api.py               # 規則 API（RESTful）
        templates/               # Jinja2 模板
            base.html            # 深色主題基礎版型
            dashboard.html       # 儀表板頁面
            components/
                indicator_card.html   # 指標卡片元件
                rule_designer.html    # 規則設計器元件
        static/
            css/main.css         # 深色主題樣式
            js/dashboard.js      # 卡片互動
            js/rule_designer.js  # 規則設計器互動
tests/                           # 單元測試
    __init__.py
    test_main.py                 # main 模組測試
    test_models.py               # 資料模型測試
    test_services.py             # 服務層測試
    test_web.py                  # Flask 路由與 API 測試
docker/                          # Docker 相關
    Dockerfile                   # Python 3.12 base image
    build.sh                     # 建立 image 腳本
logs/                            # log 輸出目錄
    .gitkeep
run.sh                           # 啟動 Web 儀表板腳本（Docker）
requirements.txt                 # Python 依賴清單
```

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
可透過環境變數 `HOST_PORT` 自訂對外埠號：

```bash
HOST_PORT=8080 bash run.sh
```

### 功能說明

- **績效指標卡片**：展示 8 項股市績效指標（勝率、獲利因子、期望值等）
- **規則設計器**：可新增/刪除進出場規則群組與條件，支援多種技術指標（MA、RSI、MACD、KD、布林通道）

### API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/indicators/<type>/params` | 取得指標可選參數 |
| GET | `/api/rules` | 列出所有規則群組 |
| POST | `/api/rules` | 建立規則群組 |
| POST | `/api/rules/<id>/conditions` | 新增條件 |
| DELETE | `/api/rules/<id>/conditions/<cid>` | 刪除條件 |

### 執行單元測試

先建立 Docker image，再於容器中執行測試：

```bash
docker run --rm tw-stock-indicator pytest tests/
```

## 授權

MIT License
