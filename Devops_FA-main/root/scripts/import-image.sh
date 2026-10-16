#!/usr/bin/env bash

set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-campus-fa2}"
SERVER_CONTAINER="k3d-${CLUSTER_NAME}-server-0"

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 IMAGE_NAME"
    echo "Example: $0 campus-event-backend:fa2"
    exit 1
fi

IMAGE_NAME="$1"

if ! docker image inspect "${IMAGE_NAME}" > /dev/null 2>&1; then
    echo "Image not found locally: ${IMAGE_NAME}"
    echo "Pull or build the image before running this script."
    exit 1
fi

if ! docker inspect "${SERVER_CONTAINER}" > /dev/null 2>&1; then
    echo "k3d server container not found: ${SERVER_CONTAINER}"
    exit 1
fi

SAFE_NAME=$(echo "${IMAGE_NAME}" | tr '/:' '__')
TAR_FILE="/tmp/${SAFE_NAME}.tar"
CONTAINER_TAR="/tmp/${SAFE_NAME}.tar"

echo "Exporting image: ${IMAGE_NAME}"
docker save "${IMAGE_NAME}" -o "${TAR_FILE}"

echo "Copying image archive into ${SERVER_CONTAINER}"
docker cp \
    "${TAR_FILE}" \
    "${SERVER_CONTAINER}:${CONTAINER_TAR}"

echo "Importing image into Kubernetes containerd"
docker exec \
    "${SERVER_CONTAINER}" \
    /bin/ctr \
    --namespace k8s.io \
    images import \
    "${CONTAINER_TAR}"

echo "Removing temporary archive"
rm -f "${TAR_FILE}"

docker exec \
    "${SERVER_CONTAINER}" \
    rm -f "${CONTAINER_TAR}" || true

echo "Image imported successfully: ${IMAGE_NAME}"
