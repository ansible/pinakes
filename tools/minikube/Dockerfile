FROM docker.io/python:3.9

RUN groupadd --gid 9001 appuser \
    && useradd --home-dir /home/appuser --create-home --uid 9002 \
    --gid 9001 --shell /bin/sh --skel /dev/null appuser

RUN pip install setuptools-rust wheel ansible

WORKDIR /home/appuser/app
COPY requirements.txt ${WORKDIR}
RUN pip install -r requirements.txt
COPY . ${WORKDIR}

RUN chown -R 9002:0 ./
USER appuser

ENTRYPOINT ["/tmp/app/tools/minikube/scripts/entrypoint.sh"]

CMD ["/tmp/app/tools/minikube/scripts/server.sh"]
