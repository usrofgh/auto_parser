ARG PYTHON_VERSION=python:3.13

FROM ${PYTHON_VERSION}-slim
WORKDIR /app
COPY . .


RUN apt-get update \
    && apt-get install -y cron  && \
    pip install --no-cache-dir -r requirements.txt

COPY crontab /etc/cron.d/app-cron

RUN chmod 0644 /etc/cron.d/app-cron \
    && crontab /etc/cron.d/app-cron
