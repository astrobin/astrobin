FROM nginx:1.15

COPY docker/nginx.dev.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx.502.html /usr/share/nginx/html/502.html

