#!/bin/sh
# For development purpose only
# Set the environment variable for accessing your Automation Controller
# export ANSIBLE_CATALOG_CONTROLLER_URL=<<your controller url>>
# export ANSIBLE_CATALOG_CONTROLLER_TOKEN=<<your controller token>>
# export ANSIBLE_CATALOG_CONTROLLER_VERIFY_SSL=True|False

if [[ -z "${ANSIBLE_CATALOG_CONTROLLER_URL}" ]]
then
  echo "Please set the environment variable ANSIBLE_CATALOG_CONTROLLER_URL"
  exit 1
fi

if [[ -z "${ANSIBLE_CATALOG_CONTROLLER_TOKEN}" ]]
then
  echo "Please set the environment variable ANSIBLE_CATALOG_CONTROLLER_TOKEN"
  exit 1
fi

if [[ -z "${ANSIBLE_CATALOG_CONTROLLER_VERIFY_SSL}" ]]
then
  echo "Please set the environment variable ANSIBLE_CATALOG_CONTROLLER_VERIFY_SSL"
  exit 1
fi

kubectl get namespace catalog 2>> /dev/null
if [ $? -ne 0 ]; then
	kubectl create namespace catalog
fi

kubectl get configmap --namespace=catalog dbscripts 2>> /dev/null
if [ $? -ne 0 ]; then
	kubectl create --namespace=catalog configmap dbscripts --from-file=./tools/minikube/templates/scripts
fi

kubectl get configmap --namespace=catalog ansible-controller-env 2>> /dev/null
if [ $? -eq 0 ]; then
	kubectl delete --namespace=catalog configmap ansible-controller-env
fi

kubectl create configmap --namespace=catalog ansible-controller-env --from-literal=ANSIBLE_CATALOG_CONTROLLER_URL="$ANSIBLE_CATALOG_CONTROLLER_URL" --from-literal=ANSIBLE_CATALOG_CONTROLLER_TOKEN="$ANSIBLE_CATALOG_CONTROLLER_TOKEN" --from-literal=ANSIBLE_CATALOG_CONTROLLER_VERIFY_SSL="$ANSIBLE_CATALOG_CONTROLLER_VERIFY_SSL"
kubectl apply --namespace=catalog -f ./tools/minikube/templates/redis-deployment.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/redis-service.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/pg-data-persistentvolumeclaim.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/postgres-deployment.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/postgres-service.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/keycloak-deployment.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/keycloak-service.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/app-claim0-persistentvolumeclaim.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/app-deployment.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/app-service.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/ingress.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/worker-claim0-persistentvolumeclaim.yaml
kubectl apply --namespace=catalog -f ./tools/minikube/templates/worker-deployment.yaml
