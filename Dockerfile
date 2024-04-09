# syntax=docker/dockerfile:1
# FROM python:3.11
FROM ubuntu:22.04
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get dist-upgrade -y && \
    apt-get clean && \
    apt-get install -y \
    git \
    pkg-config \
    libxmlsec1-openssl\
    libxml2-dev \
    libxmlsec1-dev \  
    python-setuptools \
    python3.11-dev \
    python3-venv \
    python3-pip \
    postgresql-client \
    nano

WORKDIR /hiris
COPY requirements.txt /hiris/
RUN ln -s /usr/bin/python3.10 /usr/bin/python
RUN pip install -r requirements.txt
COPY . /hiris/
EXPOSE 8000