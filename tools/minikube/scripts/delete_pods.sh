#!/bin/sh
pvs=$(kubectl get pv | grep catalog/ | awk '{print $1}')
kubectl delete namespace catalog
for pv in "$pvs"
do
    kubectl delete pv $pv
done
