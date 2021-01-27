FROM python:3.6-slim

USER root

WORKDIR /app

RUN apt-get update && \
    apt-get install -y git

# load app contents
COPY . /app

RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt

# container port
EXPOSE 8050

ENV NAME Explorer

# deploy app in flask app
CMD ["python", "dash_app.py"]
