pipeline {
    agent any

    environment {
        DOCKERHUB_USER = 'nishitbirade'      // <-- change this
        IMAGE_NAME     = "${DOCKERHUB_USER}/food-rescue-api"
        IMAGE_TAG      = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Source Code / Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --quiet -r requirements.txt
                    pytest -q
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t $IMAGE_NAME:$IMAGE_TAG -t $IMAGE_NAME:latest .'
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_PASS')]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker push $IMAGE_NAME:$IMAGE_TAG
                        docker push $IMAGE_NAME:latest
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh '''
                    sed "s|IMAGE_PLACEHOLDER|$IMAGE_NAME:$IMAGE_TAG|" k8s/deployment.yaml | kubectl apply -f -
                    kubectl apply -f k8s/service.yaml
                    kubectl rollout status deployment/food-rescue --timeout=120s
                '''
            }
        }

        stage('Verify') {
            steps {
                sh '''
                    kubectl get pods -l app=food-rescue
                    kubectl get deployment food-rescue
                    kubectl get svc food-rescue-svc
                    URL=http://$(minikube ip):30080
                    echo "App URL: $URL"
                    curl -fsS --retry 5 --retry-delay 3 --retry-connrefused --max-time 10 $URL/health
                    echo
                    curl -fsS --retry 5 --retry-delay 3 --retry-connrefused --max-time 10 $URL/
                '''
            }
        }
    }

    post {
        always { sh 'docker logout || true' }
    }
}
