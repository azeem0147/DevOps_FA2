Start the Project After Reopening the Codespace
1. Open the Project Folder
Shell
cd /workspaces/Devops_FA/root
2. Confirm Docker Is Running
Shell
docker info > /dev/null && echo "Docker is running"
3. Confirm the Kubernetes Cluster Exists
Shell
k3d cluster list

The output should include:

Plain Text
campus-fa2
4. Verify Kubernetes Access
Shell
kubectl get nodes

Expected node status:

Plain Text
Ready
5. Fix the Kubernetes API Address Only If Required

Run these commands only if kubectl get nodes fails.

Get the current k3d server IP:

Shell
SERVER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' k3d-campus-fa2-server-0)
echo "$SERVER_IP"

Update the Kubernetes API address:

Shell
kubectl config set-cluster k3d-campus-fa2 \
--server="https://${SERVER_IP}:6443" \
--insecure-skip-tls-verify=true

Verify again:

Shell
kubectl get nodes
 
6. Verify the Complete Kubernetes Environment
Shell
./scripts/verify-cluster.sh

The output should show:

Plain Text
Kubernetes node Ready
Backend Deployment 1/1
Frontend Deployment 3/3
Prometheus Deployment 1/1
Grafana Deployment 1/1
Backend PVC Bound
7. Start Application and Monitoring Ports
Shell
./scripts/start-ports.sh

This starts:

Plain Text
Application http://localhost:8081
Prometheus http://localhost:9091
Grafana http://localhost:3001
8. Verify the Complete System
Shell
./scripts/verify-application.sh

Expected final output:

Plain Text
All FA2 services verified successfully.
Open the Application

Open the Codespaces Ports tab and select port:

Plain Text
8081

The Campus Event application provides:

Event listing
Event searching and filtering
Event creation
Event update and deletion
Student registration
Registration search
Environment and system information

The System page should display:

Plain Text
Environment: FA2-KUBERNETES
Version: 2.0.0
Backend: Healthy
Database: Connected
Open Prometheus

Open the Codespaces Ports tab and select port:

Plain Text
9091

Check the backend target under:

Plain Text
Status
→ Target health

The target should show:

Plain Text
campus-event-backend
State: UP

Useful Prometheus queries:

PromQL
campus_http_requests_total
PromQL
rate(campus_http_requests_total[1m])
PromQL
up{job="campus-event-backend"}
PromQL
process_resident_memory_bytes{job="campus-event-backend"}
 
Open Grafana

Open the Codespaces Ports tab and select port:

Plain Text
3001

Use the following login credentials:

Plain Text
Username: admin
Password: admin

Open the dashboard from:

Plain Text
Dashboards
→ FA2 Monitoring
→ FA2 Campus Event Observability

The dashboard automatically uses Prometheus as its data source.

Verify Kubernetes Resources Manually
Check Nodes
Shell
kubectl get nodes
Check Application Resources
Shell
kubectl get pvc,deployments,pods,services -n campus-fa2
Check Backend Logs
Shell
kubectl logs \
deployment/campus-event-backend \
-n campus-fa2 \
--tail=50
Check Frontend Logs
Shell
kubectl logs \
-n campus-fa2 \
-l app=campus-event-frontend \
--prefix=true \
--tail=20
Check Prometheus Logs
Shell
kubectl logs \
deployment/prometheus \
-n campus-fa2 \
--tail=50
Check Grafana Logs
Shell
kubectl logs \
deployment/grafana \
-n campus-fa2 \
--tail=50
Kubernetes Scaling

The frontend was scaled from one replica to three replicas.

To scale the frontend again:

Shell
kubectl scale deployment campus-event-frontend \
--replicas=3 \
-n campus-fa2

Verify the scaling:

Shell
kubectl get deployments,pods -n campus-fa2

The backend must remain at one replica because the project uses SQLite persistent storage.

Kubernetes Rollout Verification

Check the frontend rollout:

Shell
kubectl rollout status \
deployment/campus-event-frontend \
-n campus-fa2

Check rollout history:

Shell
kubectl rollout history \
deployment/campus-event-frontend \
-n campus-fa2

Check the backend rollout:

Shell
kubectl rollout status \
deployment/campus-event-backend \
-n campus-fa2
Run Automated Tests

Install backend dependencies:

Shell
python -m pip install \
-r docker/backend/requirements.txt

Validate Python syntax:

Shell
python -m py_compile \
docker/backend/app.py \
docker/backend/test_app.py

Run all automated tests:

Shell
pytest -v docker/backend/test_app.py

Expected result:

Plain Text
7 passed
Reproducibility Scripts

The following scripts are included:

Plain Text
scripts/import-image.sh
scripts/verify-cluster.sh
scripts/start-ports.sh
scripts/stop-ports.sh
scripts/verify-application.sh
Import an Image Into k3d

Example:

Shell
./scripts/import-image.sh campus-event-backend:fa2
Verify the Kubernetes Cluster
Shell
./scripts/verify-cluster.sh
Start All Ports
Shell
./scripts/start-ports.sh
Verify All Services
Shell
./scripts/verify-application.sh
Stop All Ports
Shell
./scripts/stop-ports.sh
Stop the Codespace Safely

Before stopping the Codespace, stop the forwarding processes:

Shell
cd /workspaces/Devops_FA/root
./scripts/stop-ports.sh

Verify all project changes are committed:

Shell
cd /workspaces/Devops_FA
git status

Expected:

Plain Text
nothing to commit, working tree clean

Then stop the Codespace without deleting it.