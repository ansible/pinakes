#!/bin/bash
while true;
do echo "Waiting for keycloak setup to finish...";
    if [[ -f ansible_catalog/settings/local_keycloak.py ]]; then
        break;
    fi
    sleep 1;
done;

echo -e "\e[34m >>> Migrating changes \e[97m"
python manage.py migrate
echo -e "\e[32m >>> migration completed \e[97m"

echo -e "\e[34m >>> Start development server \e[97m"
python manage.py runserver 0.0.0.0:8000
