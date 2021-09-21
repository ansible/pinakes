FROM docker.io/python:3.9

WORKDIR /tmp/app
COPY . ${WORKDIR}

RUN mkdir /tmp/collections
ENV ANSIBLE_CFG=/tmp/.ansible \
    ANSIBLE_COLLECTIONS_PATH=/tmp/collections \
    ANSIBLE_COLLECTIONS_PATHS=/tmp/collections \
    ANSIBLE_LOCAL_TEMP=/tmp

RUN pip install ansible

RUN ansible-galaxy collection install community.general mkanoor.catalog_keycloak

ENTRYPOINT ["/tmp/app/tools/docker-compose/scripts/entrypoint.sh"]
CMD ["/tmp/app/tools/docker-compose/scripts/keycloak-setup.sh"]
