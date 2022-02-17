FROM registry.access.redhat.com/ubi8/python-39
ARG USER_ID=${USER_ID:-1001}
ARG CATALOG_KEYCLOAK_VERSION=${CATALOG_KEYCLOAK_VERSION:-1.0.20}

USER 0

RUN pip install wheel ansible

WORKDIR $HOME
COPY . $WORKDIR

RUN chown -R 1001 ./
USER $USER_ID

RUN pip install -r requirements.txt
RUN ansible-galaxy collection install community.general mkanoor.catalog_keycloak:${CATALOG_KEYCLOAK_VERSION}

ENTRYPOINT ["/opt/app-root/src/tools/docker/scripts/entrypoint.sh"]

CMD ["/opt/app-root/src/tools/docker/scripts/server.sh"]
