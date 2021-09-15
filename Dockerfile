FROM python:3.9

WORKDIR /tmp/app

COPY . ${WORKDIR}

RUN pip install -r requirements.txt

ENTRYPOINT ["docker/entrypoint.sh"]

CMD ["docker/server.sh"]
