#!/bin/bash

echo -e "\e[34m >>> Installing keycloak setup collections \e[97m"
mkdir /tmp/collections
export ANSIBLE_CFG=/tmp/.ansible
export ANSIBLE_COLLECTIONS_PATH=/tmp/collections
export ANSIBLE_COLLECTIONS_PATHS=/tmp/collections
export ANSIBLE_LOCAL_TEMP=/tmp

ansible-galaxy collection install community.general
ansible-galaxy collection install mkanoor.catalog_keycloak
ansible-playbook -vvv keycloak_setup/dev_worker.yml

echo -e "\e[34m >>> Starting worker \e[97m"
python manage.py rqworker default
