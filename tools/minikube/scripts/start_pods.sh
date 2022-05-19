#!/bin/bash
# For development purpose only
# Set the environment variable for accessing your Automation Controller

set -o nounset
set -o errexit

OVERRIDE_ENV_FILE="minikube_env_vars"
PINAKES_CONTROLLER_URL=${PINAKES_CONTROLLER_URL:-}
PINAKES_CONTROLLER_TOKEN=${PINAKES_CONTROLLER_TOKEN:-}
PINAKES_CONTROLLER_VERIFY_SSL=${PINAKES_CONTROLLER_VERIFY_SSL:-}

setup_env_vars() {
    # This is one time migration to using the env var file
    # if the file doesn't exist we create a file from the old
    # required env vars.
    if [[ ! -f "$OVERRIDE_ENV_FILE" ]]
    then
      cp ./tools/minikube/env_vars.sample "$OVERRIDE_ENV_FILE"
      if [[ -z "${PINAKES_CONTROLLER_URL}" ]]
      then
        echo "Error: Environment variable PINAKES_CONTROLLER_URL is not set."
        exit 1
      fi

      if [[ -z "${PINAKES_CONTROLLER_TOKEN}" ]]
      then
        echo "Error: Environment variable PINAKES_CONTROLLER_TOKEN is not set."
        exit 1
      fi

      if [[ -z "${PINAKES_CONTROLLER_VERIFY_SSL}" ]]
      then
        echo "Error: Environment variable PINAKES_CONTROLLER_VERIFY_SSL is not set."
        exit 1
      fi

      # To handle compatibility issues between sed on Mac and linux don't use the -i
      tmpfile=$(mktemp /tmp/pinakes_env_var.XXXXXX)
      sed -e '/PINAKES_CONTROLLER_URL/d' -e '/PINAKES_CONTROLLER_TOKEN/d' -e '/PINAKES_CONTROLLER_VERIFY_SSL/d' "$OVERRIDE_ENV_FILE" > "$tmpfile"
      mv "$tmpfile" "$OVERRIDE_ENV_FILE"
      echo "PINAKES_CONTROLLER_URL="${PINAKES_CONTROLLER_URL}"" >> "$OVERRIDE_ENV_FILE"
      echo "PINAKES_CONTROLLER_TOKEN="${PINAKES_CONTROLLER_TOKEN}"" >> "$OVERRIDE_ENV_FILE"
      echo "PINAKES_CONTROLLER_VERIFY_SSL="${PINAKES_CONTROLLER_VERIFY_SSL}"" >> "$OVERRIDE_ENV_FILE"
    fi
}

#One time setup from previous approach
setup_env_vars

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

if ! kubectl get configmap --namespace=catalog pinakes-env-overrides &>/dev/null; then
     kubectl create configmap \
	--namespace=catalog \
	pinakes-env-overrides \
	--from-env-file="$OVERRIDE_ENV_FILE"
fi



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
