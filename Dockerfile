# syntax=docker/dockerfile:1
FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /hiris
RUN apt-get update
RUN apt-get -y install libxml2-dev libxmlsec1-dev=1.2.37-2 libxmlsec1-openssl=1.2.37-2 postgresql-client nano
COPY requirements.txt /hiris/
RUN pip install -r requirements.txt
COPY . /hiris/
EXPOSE 8000