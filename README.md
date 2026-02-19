# Tw Stock Indicator

台灣股票技術指標分析工具。

## 專案架構

```
tw_stock_indicator/          # 主程式套件
    __init__.py              # 套件初始化，定義版本號
    main.py                  # 程式進入點
    logger.py                # logging 配置模組
tests/                       # 單元測試
    __init__.py
    test_main.py             # main 模組測試
docker/                      # Docker 相關
    Dockerfile               # Python 3.12 base image
    build.sh                 # 建立 image 腳本
logs/                        # log 輸出目錄
    .gitkeep
run.sh                       # 啟動主程式腳本（Docker）
requirements.txt             # Python 依賴清單
```

## 使用方法

### 建立 Docker Image

```bash
bash docker/build.sh
```

### 執行主程式

```bash
bash run.sh
```

執行後 log 檔會輸出至 `logs/` 目錄。

### 執行單元測試

先建立 Docker image，再於容器中執行測試：

```bash
docker run --rm tw-stock-indicator pytest tests/
```

## 授權

MIT License
