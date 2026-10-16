#!/usr/bin/env bash

set -euo pipefail

NAMESPACE="${NAMESPACE:-campus-fa2}"

echo "========================================"
echo "Kubernetes Nodes"
echo "========================================"

kubectl get nodes -o wide

echo
echo "========================================"
echo "Kubernetes System Pods"
echo "========================================"

kubectl get pods -n kube-system

echo
echo "========================================"
echo "Storage Classes"
echo "========================================"

kubectl get storageclass

echo
echo "========================================"
echo "FA2 Persistent Volume Claims"
echo "========================================"

kubectl get pvc -n "${NAMESPACE}"

echo
echo "========================================"
echo "FA2 Deployments"
echo "========================================"

kubectl get deployments -n "${NAMESPACE}"

echo
echo "========================================"
echo "FA2 Pods"
echo "========================================"

kubectl get pods -n "${NAMESPACE}" -o wide

echo
echo "========================================"
echo "FA2 Services"
echo "========================================"

kubectl get services -n "${NAMESPACE}"

echo
echo "Cluster verification completed."
