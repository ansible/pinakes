#!/bin/bash

while true;
do echo -e "\e[34m >>> Waiting for postgres \e[97m"
    python -c "import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((\"$ANSIBLE_CATALOG_POSTGRES_HOST\", 5432))" && break;
    sleep 1;
done

echo -e "\e[34m >>> Migrating changes \e[97m"
python manage.py migrate || exit 1
echo -e "\e[32m >>> migration completed \e[97m"

echo -e "\e[34m >>> Collecting static files \e[97m"
python manage.py collectstatic --no-input  || exit 1

echo -e "\e[34m >>> Start development server \e[97m"
python manage.py runserver 0.0.0.0:8000 || exit 1
