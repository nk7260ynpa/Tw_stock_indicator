#!/usr/bin/env bash
#
# 啟動 Docker container 執行主程式，並掛載 logs 資料夾。

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly IMAGE_NAME="tw-stock-indicator"
readonly LOGS_DIR="${SCRIPT_DIR}/logs"

# 確保 logs 目錄存在
mkdir -p "${LOGS_DIR}"

echo "=== 啟動 ${IMAGE_NAME} ==="
docker run --rm \
  -v "${LOGS_DIR}:/app/logs" \
  "${IMAGE_NAME}"
echo "=== 執行完畢 ==="
