FROM nginx:alpine

RUN apk update && apk add --no-cache certbot

ARG ENV
COPY docker/nginx-${ENV}.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx.crontab /var/spool/cron/crontabs/certbot-renew
