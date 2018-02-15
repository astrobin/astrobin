FROM nginx:alpine

# ENV should be one of: prod, local
ARG ENV
RUN apt-get update \
    && apt-get install -y python-certbot-nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY docker/nginx-${ENV}.conf /etc/nginx/conf.d/default.conf
