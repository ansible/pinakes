#!/bin/sh
# This script is used to re-deploy the catalog app and worker in your
# minikube dev environment. It builds the image in minikube and applies
# the app and worker deployments leaving the external dependencies
# Keycloak, Redis and Postgres alone. If you have local code changes
# they will be incorporated into the image.
#
set -e
echo "Rebuilding app image"
eval $(minikube -p minikube docker-env)
minikube image build -t localhost/ansible-catalog -f tools/docker/Dockerfile .
kubectl rollout restart --namespace=catalog -f ./tools/minikube/templates/app-deployment.yaml
kubectl rollout restart --namespace=catalog -f ./tools/minikube/templates/worker-deployment.yaml
