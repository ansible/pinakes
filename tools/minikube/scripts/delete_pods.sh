#!/bin/sh
kubectl delete --namespace=catalog -f ./tools/minikube/templates/postgres-service.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/keycloak-service.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/app-service.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/app-deployment.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/keycloak-deployment.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/redis-deployment.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/redis-service.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/postgres-deployment.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/ingress.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/worker-deployment.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/pg-data-persistentvolumeclaim.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/worker-claim0-persistentvolumeclaim.yaml
kubectl delete --namespace=catalog -f ./tools/minikube/templates/app-claim0-persistentvolumeclaim.yaml
kubectl delete --namespace=catalog configmap dbscripts
