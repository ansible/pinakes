#!/bin/bash

echo -e "\e[34m >>> Start Django Rq scheduler \e[97m"
python manage.py cronjobs
