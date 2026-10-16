# Campus Event Management System - DevOps Project

A campus event web app packaged with a DevOps workflow. Students can browse and search events, register, and look up or cancel registrations. Event managers can create, edit, and delete events.

## What is included

- **Frontend:** static HTML, CSS, and JavaScript served by Nginx
- **Backend:** Flask REST API with SQLite persistence
- **Local containers:** Dockerfiles and Docker Compose
- **Infrastructure examples:** Terraform configuration for QA, UAT, and PROD Docker environments
- **Kubernetes:** deployments, services, health checks, and persistent storage
- **Observability:** Prometheus metrics and a provisioned Grafana dashboard
- **CI/CD:** GitHub Actions runs Python checks and tests, builds images, then deploys the application to a temporary Kind cluster for verification

## Run locally with Docker Compose

Requirements: Docker Desktop with the Linux container engine running and Docker Compose v2.

```powershell
cd root
docker compose up --build -d
```

Open the frontend at <http://localhost:8080>. The backend health endpoint is <http://localhost:5000/health>.

Stop the containers with:

```powershell
docker compose down
```

## Repository layout

```text
.github/workflows/     GitHub Actions pipeline
root/docker/           Frontend, Flask backend, and Dockerfiles
root/terraform/        Docker infrastructure configuration and environment values
root/kubernetes/       Application Kubernetes manifests
root/monitoring/       Prometheus and Grafana manifests and dashboard
root/scripts/          Cluster, port-forward, and application helpers
root/runguide.md       Existing k3d/Codespaces environment guide
```

## CI/CD behavior

The workflow runs for pull requests and pushes to `main`, and can also be started manually. It installs backend dependencies, validates Python syntax, runs pytest, builds both images, deploys the application to an ephemeral Kind cluster, and checks the frontend and backend health/metrics endpoints. On non-pull-request runs, it also publishes images to GitHub Container Registry.

The CI workflow deploys and verifies the application manifests. The Prometheus and Grafana manifests are provided separately under `root/monitoring`.

## Run the backend tests

```powershell
cd root
python -m pip install -r docker/backend/requirements.txt
python -m pytest -v docker/backend/test_app.py
```

## Notes

- Terraform in this repository manages Docker resources through the configured Docker provider; it does not create cloud infrastructure.
- The Grafana manifest contains demo credentials for local use. Change them before exposing Grafana outside a trusted development environment.