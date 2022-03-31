#!/bin/bash
set -e
if [[ -z "${PINAKES_SECRET_KEY}" ]]
then
    echo "Please set the environment variable PINAKES_SECRET_KEY"
    exit 1
fi

if [[ -z "${PINAKES_STATIC_ROOT}" ]]
then
    echo "Please set the environment variable PINAKES_STATIC_ROOT"
    exit 1
fi

if [[ -z "${PINAKES_KEYCLOAK_URL}" ]]
then
    echo "Please set the environment variable PINAKES_KEYCLOAK_URL"
    exit 1
fi


echo -e "\e[34m >>> Migrating changes \e[97m"
python manage.py migrate
echo -e "\e[32m >>> migration completed \e[97m"

echo -e "\e[32m >>> Fetch UI tar\e[97m"

if [[ -f overrides/ui/catalog-ui.tar.gz ]]
then
	echo "Overriding with local ui tar"
	cp overrides/ui/catalog-ui.tar.gz .
else
	echo "Downloading ui tar"
        curl -o catalog-ui.tar.gz -L https://github.com/ansible/pinakes-ui/releases/download/latest/catalog-ui.tar.gz
fi

rm -rf pinakes/ui/catalog
mkdir -p pinakes/ui/catalog
tar -xf catalog-ui.tar.gz --directory pinakes/ui/catalog

# Overlay the catalog and approval images from overrides
if [[ -d overrides/pinakes ]]
then
	cp overrides/pinakes/* pinakes/ui/catalog/fonts
fi

if [[ -d overrides/approval ]]
then
	cp overrides/approval/* pinakes/ui/catalog/approval/fonts
fi

rm -rf "$PINAKES_STATIC_ROOT"

echo -e "\e[34m >>> Collect static files \e[97m"
python manage.py collectstatic

echo -e "\e[34m >>> Start gunicorn server \e[97m"
gunicorn --workers=${PINAKES_NUM_PROCS:-3} --bind 0.0.0.0:8000 pinakes.wsgi --log-level=debug
