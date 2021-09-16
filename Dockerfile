FROM docker.io/python:3.9
USER root
RUN groupadd --gid 9001 appuser \
    && useradd --home-dir /home/appuser --create-home --uid 9002 \
        --gid 9001 --shell /bin/sh --skel /dev/null appuser

RUN pip install setuptools-rust wheel ansible

RUN mkdir /home/appuser/app

WORKDIR /home/appuser/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /home/appuser/app

RUN chown -R 9002:0 ./
USER appuser

ENTRYPOINT ["/home/appuser/app/docker/entrypoint.sh"]

CMD ["/home/appuser/app/docker/server.sh"]
