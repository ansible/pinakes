FROM docker.io/python:3.9

WORKDIR /tmp/app
COPY requirements.txt ${WORKDIR}
RUN pip install -r requirements.txt
COPY . ${WORKDIR}


ENTRYPOINT ["/tmp/app/tools/docker-compose/scripts/entrypoint.sh"]

CMD ["/tmp/app/tools/docker-compose/scripts/server.sh"]
