#!/usr/bin/env bash
#
# 透過 docker compose 啟動 Web 儀表板，連接 MySQL 資料庫。

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOGS_DIR="${SCRIPT_DIR}/logs"
readonly COMPOSE_FILE="${SCRIPT_DIR}/docker/docker-compose.yaml"

# 確保 logs 目錄存在
mkdir -p "${LOGS_DIR}"

echo "=== 啟動 Web 儀表板 ==="
docker compose -f "${COMPOSE_FILE}" up
echo "=== 執行完畢 ==="
