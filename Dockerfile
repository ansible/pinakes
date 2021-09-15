FROM docker.io/python:3.9

RUN mkdir /tmp/app
WORKDIR /tmp/app

COPY . /tmp/app

RUN pip install -r requirements.txt

ENTRYPOINT ["/tmp/app/docker/entrypoint.sh"]

CMD ["/tmp/app/docker/server.sh"]
