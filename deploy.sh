#!/usr/bin/env bash
# ==============================================================================
# Automated Production Deployment Script for AML Shield Web Application
# ==============================================================================

set -e

APP_NAME="aml-shield-webapp"
CONTAINER_PORT=5000
HOST_PORT=5000

echo "=== [1/5] Checking Docker & Environment Prerequisites ==="
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker before deploying."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[ERROR] Docker Compose is not installed."
    exit 1
fi

echo "=== [2/5] Creating runtime data directories ==="
mkdir -p data logs models

echo "=== [3/5] Building Docker Image ==="
docker build -t ${APP_NAME}:latest .

echo "=== [4/5] Stopping existing container if running ==="
if [ "$(docker ps -q -f name=${APP_NAME})" ]; then
    echo "Stopping container ${APP_NAME}..."
    docker stop ${APP_NAME}
fi

if [ "$(docker ps -aq -f name=${APP_NAME})" ]; then
    echo "Removing container ${APP_NAME}..."
    docker rm ${APP_NAME}
fi

echo "=== [5/5] Launching new production container ==="
docker run -d \
  --name ${APP_NAME} \
  -p ${HOST_PORT}:${CONTAINER_PORT} \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/models:/app/models" \
  --restart unless-stopped \
  ${APP_NAME}:latest

echo "Waiting for health check validation..."
sleep 5

HEALTH_STATUS=$(curl -s http://localhost:${HOST_PORT}/health | grep -o '"status":"healthy"' || true)

if [ -n "$HEALTH_STATUS" ]; then
    echo "=========================================================================="
    echo "  DEPLOYMENT SUCCESSFUL!"
    echo "  AML Shield is running on http://localhost:${HOST_PORT}"
    echo "  Health Endpoint: http://localhost:${HOST_PORT}/health"
    echo "=========================================================================="
else
    echo "[WARNING] Health check endpoint did not report healthy status immediately."
    echo "Check logs using: docker logs ${APP_NAME}"
fi
