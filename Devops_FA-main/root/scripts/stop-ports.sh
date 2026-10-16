#!/usr/bin/env bash

set -euo pipefail

LOG_DIRECTORY="/tmp/fa2-port-forward"

for service in application prometheus grafana; do
    PID_FILE="${LOG_DIRECTORY}/${service}.pid"

    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")

        if kill -0 "${PID}" 2>/dev/null; then
            echo "Stopping ${service} port-forward, PID ${PID}"
            kill "${PID}" || true
        fi

        rm -f "${PID_FILE}"
    fi
done

pkill -f \
    "kubectl port-forward.*service/frontend.*8081:80" \
    2>/dev/null || true

pkill -f \
    "kubectl port-forward.*service/prometheus.*9091:9090" \
    2>/dev/null || true

pkill -f \
    "kubectl port-forward.*service/grafana.*3001:3000" \
    2>/dev/null || true

echo "FA2 port-forward processes stopped."
