FROM nginx:latest

COPY docker/nginx.dev.conf /etc/nginx/conf.d/default.conf

