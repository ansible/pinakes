FROM python:3.9

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

ENTRYPOINT ["/app/docker/entrypoint.sh"]

CMD ["/app/docker/server.sh"]