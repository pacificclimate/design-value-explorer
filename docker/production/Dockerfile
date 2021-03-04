FROM python:3.6-slim

RUN apt-get update && \
    apt-get install -y git
# TODO: pip install --upgrade pip

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

RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt
RUN pip install -e git+https://github.com/pacificclimate/climpyrical.git#egg=climpyrical
# requirements.txt contains a line for clympirical, but it is not installed (???)
# after the first pip install. The second one fixes that. An ugly mystery.

# Flask app port
EXPOSE 5000

ENV NAME Explorer

# On container startup, the entrypoint installs the local codebase
ENTRYPOINT /app/docker/production/entrypoint.sh
