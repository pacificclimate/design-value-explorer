FROM python:3.8-slim
LABEL Maintainer="Rod Glover <rglover@uvic.ca>"

RUN apt-get update && \
    apt-get install -y git && \
    pip install --upgrade pip pipenv

ARG RUN_GROUP=dve
ARG RUN_USER=dve
ARG RUN_HOME=/app

RUN groupadd -r ${RUN_GROUP} && \
    useradd -g ${RUN_GROUP} -d ${RUN_HOME} ${RUN_USER} && \
    mkdir ${RUN_HOME} && \
    chown ${RUN_GROUP}:${RUN_USER} ${RUN_HOME}
USER ${RUN_USER}

WORKDIR ${RUN_HOME}
COPY --chown=${RUN_GROUP}:${RUN_USER} . /app

RUN pipenv install

# Flask app port
EXPOSE 5000

ENV NAME Explorer

CMD /app/.local/bin/gunicorn \
    --config /app/docker/production/gunicorn.conf \
    --log-config /app/docker/production/logging.conf \
    dve_app:server
