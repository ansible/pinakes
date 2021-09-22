FROM docker.io/python:3.9
RUN groupadd --gid 1000 appgroup \
    && useradd --home-dir /home/appuser --create-home --uid 1000 \
        --gid 1000 --shell /bin/sh appuser

RUN pip install wheel ansible

WORKDIR /home/appuser/catalog
COPY . $WORKDIR

RUN chown -R appuser:appgroup ./
USER appuser

RUN pip install -r requirements.txt
RUN ansible-galaxy collection install community.general mkanoor.catalog_keycloak

ENTRYPOINT ["/home/appuser/catalog/docker/entrypoint.sh"]

CMD ["/home/appuser/catalog/docker/server.sh"]
