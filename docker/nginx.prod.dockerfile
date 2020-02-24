FROM nginx:1.15

COPY docker/localhost.crt /etc/ssl/certs/localhost.crt
COPY docker/localhost.key /etc/ssl/private/localhost.key
COPY docker/nginx.prod.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx.ssl.conf /etc/nginx/conf.d/ssl.conf

