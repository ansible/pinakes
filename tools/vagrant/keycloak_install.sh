#!/bin/sh
set -e
source /vagrant_data/env_vars
subscription-manager register --username $RHN_USER --password $RHN_PASSWORD --auto-attach
yum update -y
yum install -y java-11-openjdk
curl -o keycloak-16.1.1.tar.gz -L https://github.com/keycloak/keycloak/releases/download/16.1.1/keycloak-16.1.1.tar.gz
tar -xf keycloak-16.1.1.tar.gz -C /opt
/opt/keycloak-16.1.1/bin/add-user-keycloak.sh -r master -u admin -p admin
adduser keycloak
chown keycloak:keycloak -R /opt/keycloak-16.1.1
cp /vagrant_data/keycloak/services/keycloak.service /etc/systemd/system

mkdir -p /opt/keycloak-16.1.1/themes/pinakes/login/resources/{css,img}
cp /src/tools/keycloak_setup/login_theme/theme.properties "/opt/keycloak-16.1.1/themes/pinakes/login"
cp /src/tools/keycloak_setup/login_theme/background.png "/opt/keycloak-16.1.1/themes/pinakes/login/resources/img"
cp /src/tools/keycloak_setup/login_theme/styles.css "/opt/keycloak-16.1.1/themes/pinakes/login/resources/css"
chown keycloak:keycloak -R /opt/keycloak-16.1.1/themes/pinakes

systemctl daemon-reload
systemctl start keycloak.service
firewall-cmd --permanent --add-port 8080/tcp
firewall-cmd --reload
