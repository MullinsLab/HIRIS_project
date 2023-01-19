# syntax=docker/dockerfile:1
FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /hiris
COPY requirements.txt /hiris/
RUN pip install -r requirements.txt
COPY . /hiris/