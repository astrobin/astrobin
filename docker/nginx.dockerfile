FROM nginx
# ENV should be one of: [www, beta]
ARG ENV
RUN apt-get update \
    && apt-get install -y python-certbot-nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /etc/letsencrypt/live/${ENV}.astrobin.com \
    && openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/letsencrypt/live/${ENV}.astrobin.com/privkey.pem \
    -out /etc/letsencrypt/live/${ENV}.astrobin.com/fullchain.pem \
    -subj /CN=${ENV}.astrobin.com
COPY docker/nginx-${ENV}.conf /etc/nginx/conf.d/default.conf
