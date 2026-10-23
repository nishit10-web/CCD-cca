# Demo script and viva notes

## Demo order (about 5 minutes)
1. Show GitHub repo: app, tests, Dockerfile, Jenkinsfile, k8s folder.
2. Show Jenkins job (Pipeline from SCM) and the credential `dockerhub-creds` (do not reveal the token).
3. Click **Build Now**; walk through the stage view as it runs.
4. Show Docker Hub: new tag equals the Jenkins build number.
5. In the EC2 terminal: `kubectl get pods,deploy,svc` then `curl http://$(minikube ip):30080/` (shows v1).
6. Edit `VERSION = "v2"`, commit, push. Build Now again (or webhook triggers it).
7. Show new tag on Docker Hub, `kubectl get pods` (new pods), `curl` shows v2.

Handy API demo:
```
URL=http://$(minikube ip):30080
curl -X POST $URL/surplus -H 'Content-Type: application/json' -d '{"cafeteria":"Main Canteen","item":"Rice","quantity_kg":5,"lat":18.5204,"lon":73.8567}'
curl "$URL/surplus/nearby?lat=18.56&lon=73.80"
curl -X POST $URL/surplus/1/claim -H 'Content-Type: application/json' -d '{"driver":"D1","lat":18.56,"lon":73.80}'
```

## Likely viva questions
1. **Why a Jenkinsfile?** Pipeline as code: versioned with the project, repeatable, reviewable.
2. **Declarative vs scripted?** Declarative has a fixed structure (`pipeline`, `stages`); scripted is free-form Groovy.
3. **How does Jenkins get the code?** `checkout scm` clones the repo configured in the job.
4. **What does the test stage do?** Runs pytest; a failing test stops the pipeline before any image is built.
5. **Why tag with the build number?** Traceability and safe rollbacks; `latest` alone hides which version runs.
6. **How are credentials protected?** Stored in Jenkins credentials, injected with `withCredentials`, masked in logs.
7. **Pod vs Deployment vs Service?** Pod runs containers; Deployment keeps replicas and does rolling updates; Service gives a stable address and load-balances.
8. **Why NodePort?** Minikube has no cloud load balancer; NodePort exposes the app on the node IP at 30080.
9. **What is the readiness probe?** Kubernetes sends traffic only to pods whose `/health` returns OK.
10. **How did the second run update the app?** New image tag, `kubectl apply` changed the Deployment image, and a rolling update replaced the pods.
11. **Why can the jenkins user run docker?** It was added to the `docker` group (`usermod -aG docker jenkins`).
12. **A stage failed. What do you check?** Console output of that stage, then run the same command by hand on the server.

## Common fixes
- `docker: permission denied` in Jenkins: `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins`.
- `ImagePullBackOff`: Docker Hub repo is private or `DOCKERHUB_USER` is wrong; make it public.
- `kubectl` cannot connect: `sudo -u jenkins minikube start --driver=docker`.
- Minikube out of memory: use at least t3.medium.
