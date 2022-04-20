FROM registry.access.redhat.com/ubi8/nginx-120
ARG SOURCE_NGINX_CONF=nginx.conf
ARG PINAKES_UI_PACKAGE_URL=https://github.com/ansible/pinakes-ui/releases/download/latest/catalog-ui.tar.gz

ENV CERT_PATH="${NGINX_CONFIGURATION_PATH}/certs"
ENV CATALOG_UI_SRC="ui/catalog"


RUN mkdir -p ${CERT_PATH}

ADD ${SOURCE_NGINX_CONF} ${NGINX_CONFIGURATION_PATH}

# certs
ADD --chown=1001:1001 certs/*.crt ${CERT_PATH}
ADD --chown=1001:1001 certs/*.key ${CERT_PATH}

# ui files
RUN mkdir -p ${CATALOG_UI_SRC}
ADD --chown=1001:1001 ${PINAKES_UI_PACKAGE_URL} ${CATALOG_UI_SRC}/
ADD --chown=1001:1001 overrides ${CATALOG_UI_SRC}/
RUN cd ${CATALOG_UI_SRC} && tar -xf catalog-ui.tar.gz && rm -rf catalog-ui.tar.gz


CMD /usr/libexec/s2i/run
