FROM python:3.8-slim
LABEL Maintainer="Rod Glover <rglover@uvic.ca>"

RUN apt-get update && \
    apt-get install -y git libgeos-dev && \
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

# Move the Docker build arg DVE_VERSION into an
# environment variable of the same name, for consumption
# by the app. This is a long way around to getting the
# Git SHA and tag into the version number, but we don't
# run the image in a context where Git is available.
ARG DVE_VERSION
ENV DVE_VERSION $DVE_VERSION

CMD pipenv run gunicorn \
    --config /app/docker/production/gunicorn.conf \
    'dve_app:make_wsgi_app()'
