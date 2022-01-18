#!/bin/bash

echo -e "\e[34m >>> Start Django Rq worker \e[97m"
export DJANGO_SETTINGS_MODULE=ansible_catalog.settings.defaults
export ANSIBLE_CATALOG_ALLOWED_HOSTS="*"
export ANSIBLE_CATALOG_DEBUG="True"
python manage.py rqworker default
