# FA2 Deployment Notes

This directory contains the application, container, Terraform, Kubernetes, monitoring, and helper-script files used by this project.

For the project overview and Docker Compose quick start, see the [repository README](../README.md).

For instructions for the existing k3d/Codespaces cluster, service port forwarding, and manual Kubernetes checks, see [runguide.md](runguide.md).

To start the local Docker Compose environment from this directory:

```powershell
docker compose up --build -d
```

The frontend is served on port 8080 and the backend API on port 5000.