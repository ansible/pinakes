#!/bin/sh
while getopts dh flag
do
    case "${flag}" in
        d) delete_pv=1;;
        h) echo "usage: delete_pods.sh -d"; exit 0;
    esac
done

if [ -n "$delete_pv" ]; then
	pvs=($(kubectl get pv | grep catalog/ | awk '{print $1}'))
fi

kubectl delete namespace catalog

if [ -n "$delete_pv" ]; then
  for pv in "${pvs[@]}"
  do
    kubectl delete pv $pv 2> /dev/null
  done
fi
