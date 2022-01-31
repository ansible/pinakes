#! /bin/sh
set -e
source /vagrant_data/env_vars
subscription-manager register --username $RHN_USER --password $RHN_PASSWORD --auto-attach
dnf update -y
dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm
dnf -qy module disable postgresql

dnf install -y postgresql13-server postgresql13-devel redis python3.9 python39-devel

# Change python3
rm /usr/bin/python3
ln -s python3.9 /usr/bin/python3

/usr/pgsql-13/bin/postgresql-13-setup initdb
systemctl enable --now postgresql-13
sudo -u postgres psql -c "ALTER USER $ANSIBLE_CATALOG_POSTGRES_USER PASSWORD '$ANSIBLE_CATALOG_POSTGRES_PASSWORD';"

# Start Redis
systemctl enable redis
systemctl start redis

cp -R /src /opt/ansible-catalog
pip3 install -U pip

cd /opt/ansible-catalog/

if [ -d "venv" ] 
then
    rm -rf venv
fi

export PATH="$PATH:/usr/pgsql-13/bin"
python3 -m venv venv
source /opt/ansible-catalog/venv/bin/activate
pip3 install -U pip
pip3 install -r requirements.txt
pip3 install jinja2

dnf install -y ansible
ansible-galaxy collection install community.general mkanoor.catalog_keycloak
ansible-playbook -vvv tools/keycloak_setup/dev.yml

sql="CREATE DATABASE "$ANSIBLE_CATALOG_DATABASE_NAME";"
echo $sql > /tmp/my.sql
export PGPASSWORD=$ANSIBLE_CATALOG_POSTGRES_PASSWORD
psql -v ON_ERROR_STOP=1 -h "$ANSIBLE_CATALOG_POSTGRES_HOST" -U "$ANSIBLE_CATALOG_POSTGRES_USER" -f /tmp/my.sql

python3 manage.py migrate

# Fetch the UI Tar
curl -o ui.tar.xz https://raw.githubusercontent.com/lgalis/ansible-catalog-ui-build/main/catalog_ui.tar.xz
mkdir -p ansible_catalog/ui/catalog
tar -xf ui.tar.xz --directory ansible_catalog/ui/catalog

rm -rf /vagrant_data/static
rm -rf /vagrant_data/media

python3 manage.py collectstatic

python3 /vagrant_data/scripts/apply_env.py /vagrant_data/catalog/services/catalog.service.j2 /etc/systemd/system/catalog.service
python3 /vagrant_data/scripts/apply_env.py /vagrant_data/catalog/services/catalog_scheduler.service.j2 /etc/systemd/system/catalog_scheduler.service
python3 /vagrant_data/scripts/apply_env.py /vagrant_data/catalog/services/catalog_worker.service.j2 /etc/systemd/system/catalog_worker.service

adduser "$ANSIBLE_CATALOG_SERVICE_USER"
chown "$ANSIBLE_CATALOG_SERVICE_USER"."$ANSIBLE_CATALOG_SERVICE_USER" -R /opt/ansible-catalog

systemctl daemon-reload
systemctl start catalog.service
systemctl start catalog_worker.service
systemctl start catalog_scheduler.service

sudo firewall-cmd --permanent --add-port 8000/tcp
systemctl stop firewalld
systemctl start firewalld
