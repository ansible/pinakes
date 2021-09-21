#!/bin/bash

while true;
do echo "Waiting for keycloak service to come up...";
    wget http://keycloak:8080 -q -T 1 -O /dev/null >/dev/null 2>/dev/null && break;
    sleep 1;
done;
echo "Service is up!"

echo -e "\e[34m >>> Installing keycloak setup collections \e[97m"
ansible-playbook -vvv tools/keycloak_setup/dev.yml