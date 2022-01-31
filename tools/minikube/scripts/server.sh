#!/bin/bash
set -e
if [[ -z "${ANSIBLE_CATALOG_SECRET_KEY}" ]]
then
  echo "Please set the environment variable ANSIBLE_CATALOG_SECRET_KEY"
  exit 1
fi

if [[ -z "${ANSIBLE_CATALOG_STATIC_ROOT}" ]]
then
  echo "Please set the environment variable ANSIBLE_CATALOG_STATIC_ROOT"
  exit 1
fi

echo -e "\e[34m >>> Seed Kaycloak data \e[97m"
ansible-playbook -vvv tools/keycloak_setup/dev.yml

echo -e "\e[34m >>> Migrating changes \e[97m"
python manage.py migrate
echo -e "\e[32m >>> migration completed \e[97m"

echo -e "\e[32m >>> Fetch UI tar\e[97m"

curl -o ui.tar.xz https://github.com/RedHatInsights/catalog-ui/releases/download/latest/catalog-ui.tar.gz
rm -rf ansible_catalog/ui/catalog
mkdir -p ansible_catalog/ui/catalog
tar -xf ui.tar.xz --directory ansible_catalog/ui/catalog

rm -rf "$ANSIBLE_CATALOG_STATIC_ROOT"

echo -e "\e[34m >>> Collect static files \e[97m"
python manage.py collectstatic

echo -e "\e[34m >>> Start gunicorn server \e[97m"
#python manage.py runserver 0.0.0.0:8000
/home/appuser/.local/bin/gunicorn --workers=3 --bind 0.0.0.0:8000 ansible_catalog.wsgi --log-level=debug
