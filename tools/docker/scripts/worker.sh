#!/bin/bash

set -e

while true; do
    echo -e "\e[34m >>> Waiting for backend \e[97m"
    if python -c "import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('app', 8000))" &>/dev/null; then
        echo -e "\e[34m >>> Backend ready \e[97m"
        break
    fi
    sleep 1
done

echo -e "\e[34m >>> Starting worker \e[97m"
python manage.py rqworker default
