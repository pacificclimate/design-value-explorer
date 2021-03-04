FROM python:3.6-slim

USER root

WORKDIR /app
#ADD *requirements.txt ./docker/production/entrypoint.sh /app/
COPY . /app

RUN apt-get update && \
    apt-get install -y git

RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt
RUN pip install -e git+https://github.com/pacificclimate/climpyrical.git#egg=climpyrical
# requirements.txt contains a line for clympirical, but it is not installed (???)
# after the first pip install. The second one fixes that. An ugly mystery.

# Flask app port
EXPOSE 5000

ENV NAME Explorer

# On container startup, the entrypoint installs the local codebase
ENTRYPOINT /app/docker/production/entrypoint.sh
