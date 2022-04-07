#!/bin/bash
# For development purpose only
# Set the environment variable for accessing your Automation Controller
# export PINAKES_CONTROLLER_URL=<<your controller url>>
# export PINAKES_CONTROLLER_TOKEN=<<your controller token>>
# export PINAKES_CONTROLLER_VERIFY_SSL=True|False

set -o nounset
set -o errexit

PINAKES_CONTROLLER_URL=${PINAKES_CONTROLLER_URL:-}
PINAKES_CONTROLLER_TOKEN=${PINAKES_CONTROLLER_TOKEN:-}
PINAKES_CONTROLLER_VERIFY_SSL=${PINAKES_CONTROLLER_VERIFY_SSL:-}

if [[ -z "${PINAKES_CONTROLLER_URL}" ]]; then
  echo "Error: Environment variable PINAKES_CONTROLLER_URL is not set."
  exit 1
fi

if [[ -z "${PINAKES_CONTROLLER_TOKEN}" ]]; then
  echo "Error: Environment variable PINAKES_CONTROLLER_TOKEN is not set."
  exit 1
fi

if [[ -z "${PINAKES_CONTROLLER_VERIFY_SSL}" ]]; then
  echo "Error: Environment variable PINAKES_CONTROLLER_VERIFY_SSL is not set."
  exit 1
fi

# Set the environment variable for accessing insights service
# export PINAKES_INSIGHTS_TRACKING_STATE=True|False
# export PINAKES_INSIGHTS_URL=<<your insights url>>
# export PINAKES_INSIGHTS_USERNAME=<<your insights username>>
# export PINAKES_INSIGHTS_PASSWORD=<<your insights password>>

# Check if metrics collection is turned on
PINAKES_INSIGHTS_TRACKING_STATE=${PINAKES_INSIGHTS_TRACKING_STATE:-False}
PINAKES_INSIGHTS_URL=${PINAKES_INSIGHTS_URL:-}
PINAKES_INSIGHTS_USERNAME=${PINAKES_INSIGHTS_USERNAME:-}
PINAKES_INSIGHTS_PASSWORD=${PINAKES_INSIGHTS_PASSWORD:-}

if [[ "${PINAKES_INSIGHTS_TRACKING_STATE}" = "True" ]]; then
  if [[ -z "${PINAKES_INSIGHTS_URL}" ]]; then
    echo "Error: Environment variable PINAKES_INSIGHTS_URL is not set."
    exit 1
  fi

  if [[ -z "${PINAKES_INSIGHTS_USERNAME}" ]]; then
    echo "Error: Environment variable PINAKES_INSIGHTS_USERNAME is not set."
    exit 1
  fi

  if [[ -z "${PINAKES_INSIGHTS_PASSWORD}" ]]; then
    echo "Error: Environment variable PINAKES_INSIGHTS_PASSWORD is not set."
    exit 1
  fi
fi

if ! kubectl get namespace catalog &>/dev/null; then
	kubectl create namespace catalog
fi

if ! kubectl get configmap --namespace=catalog dbscripts &>/dev/null; then
	kubectl create --namespace=catalog configmap dbscripts --from-file=./tools/minikube/templates/scripts
fi

if ! kubectl get configmap --namespace=catalog catalog-nginx.conf &>/dev/null; then
	kubectl create --namespace=catalog configmap catalog-nginx.conf --from-file=./tools/minikube/nginx
fi

if ! kubectl get configmap --namespace=catalog ssl &>/dev/null; then
	kubectl create --namespace=catalog configmap ssl \
        --from-file='./tools/minikube/nginx/pinakes.k8s.local.key' \
        --from-file='./tools/minikube/nginx/pinakes.k8s.local.crt'
fi

if ! kubectl get configmap --namespace=catalog postgresql &>/dev/null; then
     kubectl create configmap postgresql --from-file=./tools/postgresql -n catalog
fi

if kubectl get configmap --namespace=catalog ansible-controller-env &>/dev/null; then
	kubectl delete --namespace=catalog configmap ansible-controller-env
fi

if kubectl get configmap --namespace=catalog ansible-insights-env &>/dev/null; then
	kubectl delete --namespace=catalog configmap ansible-insights-env
fi

# Override Keycloak image files
tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)
cp ./tools/keycloak_setup/login_theme/* "$tmp_dir"
if [[ -d ./overrides/keycloak ]]; then
	cp ./overrides/keycloak/* "$tmp_dir"
fi
 
if ! kubectl get configmap --namespace=catalog keycloak-theme &>/dev/null; then
     kubectl create configmap keycloak-theme --from-file="$tmp_dir" -n catalog
fi

rm -rf $tmp_dir

kubectl create configmap \
    --namespace=catalog \
    ansible-controller-env \
    --from-literal=PINAKES_CONTROLLER_URL="$PINAKES_CONTROLLER_URL" \
    --from-literal=PINAKES_CONTROLLER_TOKEN="$PINAKES_CONTROLLER_TOKEN" \
    --from-literal=PINAKES_CONTROLLER_VERIFY_SSL="$PINAKES_CONTROLLER_VERIFY_SSL"

kubectl create configmap \
    --namespace=catalog \
    ansible-insights-env \
    --from-literal=PINAKES_INSIGHTS_TRACKING_STATE="$PINAKES_INSIGHTS_TRACKING_STATE" \
    --from-literal=PINAKES_INSIGHTS_URL="$PINAKES_INSIGHTS_URL" \
    --from-literal=PINAKES_INSIGHTS_USERNAME="$PINAKES_INSIGHTS_USERNAME" \
    --from-literal=PINAKES_INSIGHTS_PASSWORD="$PINAKES_INSIGHTS_PASSWORD"

# Build the image if the user hasn't built it yet
if ! minikube image ls | grep pinakes:latest; then
    echo "Building app image"
    eval $(minikube -p minikube docker-env)
    minikube image build -t localhost/pinakes -f tools/docker/Dockerfile .
fi

kubectl apply --namespace=catalog -f ./tools/minikube/templates/redis-deployment.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/redis-service.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/pg-data-persistentvolumeclaim.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/postgres-deployment.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/postgres-service.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/keycloak-deployment.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/keycloak-service.yaml

kubectl apply --namespace=catalog -f ./tools/minikube/templates/keycloak-setup.yml

echo "We are adding roles, groups, users, permissions into Keycloak"
echo "Waiting for Keycloak setup job to end, this could take a couple of minutes ....."
if ! kubectl -n catalog wait --for=condition=complete --timeout=8m job/keycloak-setup; then
	echo "Could not wait for keycloak setup"
	echo "run delete_pods.sh -d"
	exit 1
fi

kubectl apply --namespace=catalog -f ./tools/minikube/templates/app-claim0-persistentvolumeclaim.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/app-deployment.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/app-service.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/nginx-deployment.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/nginx-service.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/ingress.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/worker-claim0-persistentvolumeclaim.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/worker-deployment.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/scheduler-claim0-persistentvolumeclaim.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/scheduler-deployment.yaml
