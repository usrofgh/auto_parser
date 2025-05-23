ARG PYTHON_VERSION=python:3.13
FROM ${PYTHON_VERSION}-slim

ENV PYTHONPATH=/app:${PYTHONPATH}
WORKDIR /app
COPY . .

RUN apt-get update  \
    && apt-get install -y cron  \
    && apt-get install -y --no-install-recommends postgresql-client  \
    && pip install -r requirements.txt

COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN touch /var/log/cron.log
