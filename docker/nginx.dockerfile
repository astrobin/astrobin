FROM nginx
# ENV should be one of: [prod, beta]
ARG ENV
RUN apt-get update && apt-get install -y python-certbot-nginx
COPY docker/nginx-${ENV}.conf /etc/nginx/conf.d/default.conf
