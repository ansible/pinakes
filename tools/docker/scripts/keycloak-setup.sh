#!/bin/bash
set -e
KEYCLOAK_SETUP_VERSION=1.0.28
KEYCLOAK_SEED_FILE=${KEYCLOAK_SEED_FILE:-tools/keycloak_setup/dev.yml}
EXTRA_OPTS=""
DEBUG_MODE=$(echo "$PINAKES_DEBUG" | tr '[:upper:]' '[:lower:]')

if [[ $DEBUG_MODE == "true" ]]; then
    EXTRA_OPTS="-vvv"
fi

echo running > /startup/status

while true;
do echo "Waiting for keycloak service to come up...";
    wget --no-check-certificate $PINAKES_KEYCLOAK_URL -q -T 1 -O /dev/null >/dev/null 2>/dev/null && break;
    sleep 3;
done;
echo "Service is up!"

echo -e "\e[34m >>> Building keycloak setup collections \e[97m"
rm -rf pinakes-keycloak_setup-"$KEYCLOAK_SETUP_VERSION".tar.gz
ansible-galaxy collection build tools/keycloak_setup/collection
echo -e "\e[34m >>> Installing keycloak setup collections \e[97m"
ansible-galaxy collection install community.general pinakes-keycloak_setup-"$KEYCLOAK_SETUP_VERSION".tar.gz
echo -e "\e[34m >>> Configuring Keycloak \e[97m"
ansible-playbook ${KEYCLOAK_SEED_FILE} ${EXTRA_OPTS}
echo finished > /startup/status
