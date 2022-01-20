#!/bin/bash
set -e
echo -e "\e[34m >>> Seed Kaycloak data \e[97m"
ansible-playbook -vvv tools/keycloak_setup/dev.yml
echo -e "\e[34m >>> Migrating changes \e[97m"
python manage.py migrate
echo -e "\e[32m >>> migration completed \e[97m"

echo -e "\e[32m >>> Create Source object\e[97m"
python manage.py shell < tools/minikube/scripts/initialize_source.py

echo -e "\e[32m >>> Fetch UI tar\e[97m"
curl -o ui.tar.xz https://raw.githubusercontent.com/lgalis/ansible-catalog-ui-build/main/ui.tar.xz
mkdir -p /app/ui
tar -xf ui.tar.xz --directory /app/ui

echo -e "\e[34m >>> Start gunicorn server \e[97m"
#python manage.py runserver 0.0.0.0:8000
/home/appuser/.local/bin/gunicorn --workers=3 --bind 0.0.0.0:8000 ansible_catalog.wsgi --log-level=debug
