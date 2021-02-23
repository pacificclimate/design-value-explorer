FROM python:3.6-slim

USER root

# IMPORTANT: You must mount the local codebase to this directory
WORKDIR /codebase
ADD *requirements.txt /codebase/

RUN apt-get update && \
    apt-get install -y git

RUN pip install --trusted-host pypi.python.org -r /codebase/requirements.txt \
    pip install -e git+https://github.com/pacificclimate/climpyrical.git#egg=climpyrical
# requirements.txt contains a line for clympirical, but it is not installed (???)
# after the first pip install. The second one fixes that. An ugly mystery.

# Flask app port
EXPOSE 5000

ENV NAME Explorer

# On container startup, the entrypoint installs the local codebase
ENTRYPOINT /codebase/docker/dev-local/entrypoint.sh
