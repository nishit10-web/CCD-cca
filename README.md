# CCA2: CI/CD Pipeline for the Food Rescue Network (Jenkins, Docker, Kubernetes)

**Course:** Cloud Computing and DevOps (T.Y. B.Tech CSE, Sem 5, AY 2026-27)
**Student:** Zayed Shaikh, PRN 1262241091, Roll No 34, Panel A / Batch A2

## 1. Project chosen
**Institutional Food Wastage and Rapid Distribution Network**, an existing mini-project.
Cafeterias post surplus food, NGO drivers within a 10 km radius claim it, and the handover
is confirmed with a one-time password (OTP). This repository holds the project's core REST API
(FastAPI). Storage is in-memory here so the pipeline needs no database; the full project uses
PostgreSQL/PostGIS.

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health check used by Kubernetes and the Verify stage |
| `GET /` | Service name, version, radius |
| `POST /surplus` | Cafeteria posts surplus food |
| `GET /surplus/nearby?lat=&lon=` | Available listings within 10 km |
| `POST /surplus/{id}/claim` | Driver claims a listing, OTP generated |
| `POST /surplus/{id}/handover` | OTP verified, status becomes delivered |

## 2. Repository layout
```
app/            FastAPI source
tests/          pytest tests (run in the Build and Test stage)
Dockerfile      container image
Jenkinsfile     declarative pipeline
k8s/            deployment.yaml, service.yaml
aws-setup.sh    installs Docker, Jenkins, kubectl, Minikube on EC2
docs/           demo script and viva notes
```

## 3. Pipeline stages (Jenkinsfile)
1. **Checkout:** Jenkins pulls the latest code from GitHub (`checkout scm`).
2. **Build and Test:** creates a virtualenv, installs `requirements.txt`, runs `pytest` (7 tests).
3. **Docker Build:** builds `<dockerhub-user>/food-rescue-api:<build-number>` and `:latest`.
4. **Push Image:** logs in with the Jenkins credential `dockerhub-creds` and pushes both tags.
5. **Deploy to Minikube:** puts the new tag into `k8s/deployment.yaml`, applies it and `service.yaml`, waits for the rollout.
6. **Verify:** lists pods, deployment and service, then calls `/health` and `/` on the NodePort.

## 4. Jenkins on AWS (setup)
1. EC2 Ubuntu instance (t3.medium or larger, 20 GB). Security group inputs: 22, 8080, 30080.
2. Run `bash aws-setup.sh` (installs Java, Docker, Jenkins, kubectl, Minikube; starts Minikube as the `jenkins` user).
3. Open `http://<EC2-IP>:8080`, unlock with the printed password, install suggested plugins.
4. Add credential: Username with password, ID `dockerhub-creds` (Docker Hub username and access token).
5. Create a Pipeline job, "Pipeline script from SCM", Git, this repo URL, branch `main`, path `Jenkinsfile`.

## 5. Image push
The image goes to Docker Hub as `<user>/food-rescue-api`, tagged with the Jenkins build number
(so every build is traceable) and `latest`. The repository is public so Minikube can pull it.
Credentials are stored in Jenkins and never appear in the code.

## 6. Deployment and access
`k8s/deployment.yaml` runs 2 replicas with a readiness probe on `/health`.
`k8s/service.yaml` is a NodePort Service (port 80 to container 8000, node port 30080).
On the EC2 host the app is reachable at `http://$(minikube ip):30080`. To open it from a browser:
`kubectl port-forward --address 0.0.0.0 svc/food-rescue-svc 8000:80` and open `http://<EC2-IP>:8000/docs`
(open port 8000 in the security group).

## 7. Second run (code change)
`VERSION` in `app/main.py` was changed from `"v1"` to `"v2"` and pushed. The pipeline ran again,
published image tag `<n+1>`, and Kubernetes rolled out new pods; `GET /` then returned `v2`.

## 8. Screenshots (add yours)
1. Jenkins stage view, first run (all green)
2. Docker Hub repo showing tags
3. `kubectl get pods,deploy,svc`
4. App in the browser / `curl` output (v1)
5. Jenkins stage view, second run
6. `curl` output (v2) and `kubectl describe deployment food-rescue | grep Image`
