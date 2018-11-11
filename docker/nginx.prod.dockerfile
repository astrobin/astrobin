FROM nginx:1.15

RUN apt-get update && apt-get install -y certbot && apt-get clean

COPY docker/nginx.prod.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx.ssl.conf /etc/nginx/conf.d/ssl.conf

