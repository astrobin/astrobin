FROM nginx:1.15

COPY docker/nginx.dev.conf /etc/nginx/conf.d/default.conf

