#!/bin/bash
# Run once on a fresh Ubuntu 22.04/24.04 EC2 instance (t3.medium or bigger, 20 GB disk).
# Security group: open ports 22 (SSH), 8080 (Jenkins), 30080 (app, optional).
set -e

sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 python3-venv python3-pip fontconfig openjdk-17-jre conntrack

# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Jenkins
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee /etc/apt/sources.list.d/jenkins.list
sudo apt-get update
sudo apt-get install -y jenkins
sudo usermod -aG docker jenkins

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -m 0755 kubectl /usr/local/bin/kubectl

# Minikube (must run as the jenkins user so the pipeline can use it)
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install -m 0755 minikube-linux-amd64 /usr/local/bin/minikube
sudo systemctl restart docker jenkins
sudo -u jenkins minikube start --driver=docker

echo "Jenkins initial admin password:"
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
echo "Open http://<EC2-PUBLIC-IP>:8080"
