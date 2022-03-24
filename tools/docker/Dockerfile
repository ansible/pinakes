FROM registry.access.redhat.com/ubi8/python-39
ARG USER_ID=${USER_ID:-1001}
USER 0

RUN pip install wheel ansible 

# required for compatibility between docker-compose and minikube
RUN mkdir /startup && chmod a+rwx /startup

WORKDIR $HOME
COPY . $WORKDIR

RUN chown -R 1001 ./
USER $USER_ID

RUN pip install -r requirements.txt

ENTRYPOINT ["/opt/app-root/src/tools/docker/scripts/entrypoint.sh"]

CMD ["/opt/app-root/src/tools/docker/scripts/server.sh"]
