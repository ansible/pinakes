#!/bin/bash
set -e

while true;
do echo "Waiting for keycloak service to come up...";
    wget --no-check-certificate $PINAKES_KEYCLOAK_URL/ -q -T 1 -O /dev/null >/dev/null 2>/dev/null && break;
    sleep 3;
done;
echo "Service is up!"

echo -e "\e[34m >>> Installing keycloak setup collections \e[97m"

cd tools/keycloak_setup
ansible-playbook pinakes.keycloak.dev -vvv
