#!/bin/bash

echo -e "\e[34m >>> Starting worker \e[97m"
python manage.py rqworker default
