FROM docker.io/python:3.9
ARG USER_ID=${USER_ID:-1000}
ARG CATALOG_KEYCLOAK_VERSION=${CATALOG_KEYCLOAK_VERSION:-1.0.19}
RUN groupadd --gid 1000 appgroup \
    && useradd --home-dir /home/appuser --create-home --uid 1000 \
    --gid 1000 --shell /bin/sh appuser

RUN pip install wheel ansible

WORKDIR /home/appuser/catalog
COPY . $WORKDIR

RUN chown -R appuser:appgroup ./
USER $USER_ID

RUN pip install -r requirements.txt
RUN ansible-galaxy collection install community.general mkanoor.catalog_keycloak:${CATALOG_KEYCLOAK_VERSION}

ENTRYPOINT ["/home/appuser/catalog/tools/docker/scripts/entrypoint.sh"]

CMD ["/home/appuser/catalog/tools/docker/scripts/server.sh"]
