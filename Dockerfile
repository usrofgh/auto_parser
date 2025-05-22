ARG PYTHON_VERSION=python:3.13

FROM ${PYTHON_VERSION}-slim
WORKDIR /app
COPY . .


RUN apt-get update \
    && apt-get install -y cron && \
    pip install -r requirements.txt

COPY crontab /etc/cron.d/app-cron
RUN chmod 0644 /etc/cron.d/app-cron

RUN touch /var/log/cron.log
RUN crontab /etc/cron.d/app-cron

CMD cron && tail -f /var/log/cron.log
