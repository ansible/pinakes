#!/bin/sh
set -e
source /vagrant_data/env_vars

subscription-manager register --username $RHN_USER --password $RHN_PASSWORD --auto-attach
dnf update -y

dnf install -y nginx policycoreutils-python-utils
cp /vagrant_data/nginx/ssl/catalog.vm.local.key /etc/ssl/catalog.key
cp /vagrant_data/nginx/ssl/catalog.vm.local.crt /etc/ssl/catalog.crt
pip3 install jinja2
python3 /vagrant_data/scripts/apply_env.py /vagrant_data/nginx/conf/catalog-nginx.conf.j2 /etc/nginx/conf.d/catalog-nginx.conf

chmod -R 755 /vagrant_data/static

mkdir -p /vagrant_data/media

chmod -R 755 /vagrant_data/media
systemctl enable nginx
systemctl restart nginx
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

# SE Linux Policies
# semanage permissive -a httpd_t
# Things we need
# To connect to the catalog app running on a different vm
# setsebool -P httpd_can_network_connect on

# To access static files we need this, but it fails since its mounted
# across vms
# chcon -v --type=httpd_t /vagrant_data/static

# Temporary solution
semodule -i /vagrant_data/nginx/policy/nginx.pp
