#!/bin/sh
# For development purpose only
# Set the environment variable for accessing your Automation Controller
# export PINAKES_CONTROLLER_URL=<<your controller url>>
# export PINAKES_CONTROLLER_TOKEN=<<your controller token>>
# export PINAKES_CONTROLLER_VERIFY_SSL=True|False

if [[ -z "${PINAKES_CONTROLLER_URL}" ]]
then
  echo "Please set the environment variable PINAKES_CONTROLLER_URL"
  exit 1
fi

if [[ -z "${PINAKES_CONTROLLER_TOKEN}" ]]
then
  echo "Please set the environment variable PINAKES_CONTROLLER_TOKEN"
  exit 1
fi

if [[ -z "${PINAKES_CONTROLLER_VERIFY_SSL}" ]]
then
  echo "Please set the environment variable PINAKES_CONTROLLER_VERIFY_SSL"
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

kubectl get configmap --namespace=catalog catalog-nginx.conf 2>> /dev/null
if [ $? -ne 0 ]; then
	kubectl create --namespace=catalog configmap catalog-nginx.conf --from-file=./tools/minikube/nginx
fi

kubectl get configmap --namespace=catalog ssl 2>> /dev/null
if [ $? -ne 0 ]; then
	kubectl create --namespace=catalog configmap ssl --from-file=./tools/minikube/nginx/catalog.k8s.local.key --from-file=./tools/minikube/nginx/catalog.k8s.local.crt
fi

kubectl get configmap --namespace=catalog ansible-controller-env 2>> /dev/null
if [ $? -eq 0 ]; then
	kubectl delete --namespace=catalog configmap ansible-controller-env
fi

kubectl create configmap --namespace=catalog ansible-controller-env --from-literal=PINAKES_CONTROLLER_URL="$PINAKES_CONTROLLER_URL" --from-literal=PINAKES_CONTROLLER_TOKEN="$PINAKES_CONTROLLER_TOKEN" --from-literal=PINAKES_CONTROLLER_VERIFY_SSL="$PINAKES_CONTROLLER_VERIFY_SSL"
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
kubectl -n catalog wait --for=condition=complete --timeout=8m job/keycloak-setup

if [ $? -ne 0 ]; then
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
