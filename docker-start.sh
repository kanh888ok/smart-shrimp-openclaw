#!/bin/bash
set -euo pipefail

echo "SmartShrimp OpenClaw - Docker deployment"

auto_compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    echo "Docker Compose is not installed."
    exit 1
  fi
}

command -v docker >/dev/null 2>&1 || { echo "Docker is not installed."; exit 1; }
mkdir -p data reports logs
cd docker
auto_compose build
auto_compose up -d
cd ..

echo "Dashboard: http://localhost:8501"
echo "Logs: docker compose -f docker/docker-compose.yml logs -f"
