FROM python:3.6-slim

USER root

WORKDIR /app

RUN mkdir /app/assets/

# load app contents
ADD . /app && \
    ./assets/ /app/assets

RUN pip install --trusted-host pypi.python.org -r requirements.txt

# container port
EXPOSE 8050

ENV NAME Explorer

# deploy app in flask app
CMD ["python", "dash_app.py"]