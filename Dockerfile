FROM python:3.6

USER root

WORKDIR /app

RUN mkdir /app/assets/

ADD . /app
ADD ./assets/ /app/assets

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 8050

ENV NAME Explorer

CMD ["python", "dash_app.py"]