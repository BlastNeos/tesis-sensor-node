#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="$ROOT/infrastructure/mosquitto/docker-compose.yml"

docker compose -f "$COMPOSE" exec broker \
  mosquitto_pub -h localhost -q 1 \
  -t 'meteo/sensor/lit-test' \
  -m '{"node_id":"lit-test","test":true}'
