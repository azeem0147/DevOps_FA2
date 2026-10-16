#!/usr/bin/env bash

set -euo pipefail

APPLICATION_URL="${APPLICATION_URL:-http://localhost:8081}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9091}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3001}"

echo "Checking frontend..."

curl \
    --fail \
    --silent \
    --show-error \
    --head \
    "${APPLICATION_URL}"

echo
echo "Checking backend health..."

curl \
    --fail \
    --silent \
    --show-error \
    "${APPLICATION_URL}/api-proxy/health"

echo
echo
echo "Checking backend metrics..."

curl \
    --fail \
    --silent \
    --show-error \
    "${APPLICATION_URL}/api-proxy/metrics" \
    | grep "campus_http_requests_total" \
    | head -5

echo
echo "Checking Prometheus..."

curl \
    --fail \
    --silent \
    --show-error \
    "${PROMETHEUS_URL}/-/ready"

echo
echo
echo "Checking Grafana..."

curl \
    --fail \
    --silent \
    --show-error \
    "${GRAFANA_URL}/api/health"

echo
echo
echo "All FA2 services verified successfully."
