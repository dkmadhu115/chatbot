From python:3.12.4-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt