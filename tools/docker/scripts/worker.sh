#!/bin/bash

set -e

while true; do
    echo -e "\e[34m >>> Waiting for postgres \e[97m"
    if python -c "import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((\"$ANSIBLE_CATALOG_POSTGRES_HOST\", 5432))"; then
        echo -e "\e[34m >>> Postgres ready \e[97m"
        break
    fi
    sleep 1
done


echo -e "\e[34m >>> Starting worker \e[97m"
python manage.py rqworker default
