FROM nginx:latest

RUN apt-get update && apt-get install -y certbot && apt-get clean

ARG ENV
COPY docker/nginx-${ENV}.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx.crontab /var/spool/cron/crontabs/certbot-renew
