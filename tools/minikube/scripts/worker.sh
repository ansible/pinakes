#!/bin/bash

echo -e "\e[34m >>> Seed Kaycloak data \e[97m"
ansible-playbook -vvv tools/keycloak_setup/dev_worker.yml
echo -e "\e[34m >>> Start Django Rq worker \e[97m"
python manage.py rqworker default
