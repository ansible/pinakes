#!/bin/bash

echo -e "\e[34m >>> Seed Kaycloak data \e[97m"
ansible-playbook -vvv tools/keycloak_setup/dev.yml
echo -e "\e[34m >>> Migrating changes \e[97m"
python manage.py migrate
echo -e "\e[32m >>> migration completed \e[97m"

echo -e "\e[34m >>> Start development server \e[97m"
python manage.py runserver 0.0.0.0:8000
