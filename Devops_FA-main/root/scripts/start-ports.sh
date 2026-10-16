#!/usr/bin/env bash

set -euo pipefail

NAMESPACE="${NAMESPACE:-campus-fa2}"
LOG_DIRECTORY="/tmp/fa2-port-forward"

mkdir -p "${LOG_DIRECTORY}"

stop_existing_forward() {
    local pattern="$1"

    existing_pids=$(pgrep -f "${pattern}" || true)

    if [ -n "${existing_pids}" ]; then
        echo "Stopping old port-forward process: ${pattern}"
        kill ${existing_pids} 2>/dev/null || true
    fi
}

stop_existing_forward \
    "kubectl port-forward.*service/frontend.*8081:80"

stop_existing_forward \
    "kubectl port-forward.*service/prometheus.*9091:9090"

stop_existing_forward \
    "kubectl port-forward.*service/grafana.*3001:3000"

echo "Starting Campus Event application on port 8081"

nohup kubectl port-forward \
    -n "${NAMESPACE}" \
    service/frontend \
    8081:80 \
    > "${LOG_DIRECTORY}/application.log" 2>&1 &

echo $! > "${LOG_DIRECTORY}/application.pid"

echo "Starting Prometheus on port 9091"

nohup kubectl port-forward \
    -n "${NAMESPACE}" \
    service/prometheus \
    9091:9090 \
    > "${LOG_DIRECTORY}/prometheus.log" 2>&1 &

echo $! > "${LOG_DIRECTORY}/prometheus.pid"

echo "Starting Grafana on port 3001"

nohup kubectl port-forward \
    -n "${NAMESPACE}" \
    service/grafana \
    3001:3000 \
    > "${LOG_DIRECTORY}/grafana.log" 2>&1 &

echo $! > "${LOG_DIRECTORY}/grafana.pid"

sleep 5

echo
echo "Active FA2 port-forward processes:"
ps -ef | grep "[k]ubectl port-forward" || true

echo
echo "Application: http://localhost:8081"
echo "Prometheus:  http://localhost:9091"
echo "Grafana:     http://localhost:3001"
