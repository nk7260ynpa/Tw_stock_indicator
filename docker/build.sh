#!/usr/bin/env bash
#
# 建立 nk7260ynpa/tw-stock-indicator Docker image。

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
readonly IMAGE_NAME="nk7260ynpa/tw-stock-indicator"

echo "=== 開始建立 Docker image: ${IMAGE_NAME} ==="
docker build -t "${IMAGE_NAME}" -f "${SCRIPT_DIR}/Dockerfile" "${PROJECT_DIR}"
echo "=== Docker image 建立完成: ${IMAGE_NAME} ==="
