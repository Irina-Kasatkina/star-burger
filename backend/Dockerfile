# syntax=docker/dockerfile:1

FROM python:3.10.6
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /code/
COPY requirements.txt /code/

RUN pip3 install -r requirements.txt
                                      
RUN mkdir /code/bundles/

COPY . /code/
