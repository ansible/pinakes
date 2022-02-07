#!/bin/bash
set -e

while true; do
    echo -e "\e[34m >>> Waiting for postgres \e[97m"
    if python -c "import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((\"$AUTOMATION_SERVICES_CATALOG_POSTGRES_HOST\", 5432))"; then
        echo -e "\e[34m >>> Postgres ready \e[97m"
        break
    fi
    sleep 1
done

echo -e "\e[34m >>> Migrating changes \e[97m"
python manage.py migrate || exit 1
echo -e "\e[32m >>> migration completed \e[97m"

echo -e "\e[34m >>> Collecting static files \e[97m"
python manage.py collectstatic --no-input  || exit 1

echo -e "\e[34m >>> Starting production server \e[97m"
gunicorn --workers=3 --bind 0.0.0.0:8000 ansible_catalog.wsgi --log-level=debug || exit 1
