#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="$ROOT/infrastructure/mosquitto/docker-compose.yml"

docker compose -f "$COMPOSE" exec broker \
  mosquitto_sub -h localhost -q 1 -v \
  -t 'meteo/sensor/#' \
  -t 'system/status/#'
