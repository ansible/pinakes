#!/bin/bash

echo -e "\e[34m >>> Start Django Rq worker \e[97m"
python manage.py rqworker default
