#!/bin/bash
set -e
if [[ -z "${AUTOMATION_SERVICES_CATALOG_SECRET_KEY}" ]]
then
    echo "Please set the environment variable AUTOMATION_SERVICES_CATALOG_SECRET_KEY"
    exit 1
fi

if [[ -z "${AUTOMATION_SERVICES_CATALOG_STATIC_ROOT}" ]]
then
    echo "Please set the environment variable AUTOMATION_SERVICES_CATALOG_STATIC_ROOT"
    exit 1
fi

if [[ -z "${AUTOMATION_SERVICES_CATALOG_KEYCLOAK_URL}" ]]
then
    echo "Please set the environment variable AUTOMATION_SERVICES_CATALOG_KEYCLOAK_URL"
    exit 1
fi


echo -e "\e[34m >>> Migrating changes \e[97m"
python manage.py migrate
echo -e "\e[32m >>> migration completed \e[97m"

echo -e "\e[32m >>> Fetch UI tar\e[97m"

curl -o ui.tar.xz -L https://github.com/RedHatInsights/catalog-ui/releases/download/latest/catalog-ui.tar.gz
rm -rf automation_services_catalog/ui/catalog
mkdir -p automation_services_catalog/ui/catalog
tar -xf ui.tar.xz --directory automation_services_catalog/ui/catalog

rm -rf "$AUTOMATION_SERVICES_CATALOG_STATIC_ROOT"

echo -e "\e[34m >>> Collect static files \e[97m"
python manage.py collectstatic

echo -e "\e[34m >>> Start gunicorn server \e[97m"
gunicorn --workers=3 --bind 0.0.0.0:8000 automation_services_catalog.wsgi --log-level=debug
