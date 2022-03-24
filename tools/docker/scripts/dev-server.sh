#!/bin/bash
set -e

while true; do
    echo -e "\e[34m >>> Waiting for keycloak setup \e[97m"
    if grep -q finished /startup/status; then
        echo -e "\e[34m >>> Keycloak configured \e[97m"
        break
    fi
    sleep 1
done

echo -e "\e[34m >>> Migrating changes \e[97m"
python manage.py migrate
echo -e "\e[32m >>> migration completed \e[97m"

echo -e "\e[34m >>> Collecting static files \e[97m"
python manage.py collectstatic --no-input

echo -e "\e[34m >>> Start development server \e[97m"
python manage.py runserver 0.0.0.0:8000
