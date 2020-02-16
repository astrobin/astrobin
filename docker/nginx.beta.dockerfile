FROM nginx:1.15

RUN apt-get update && apt-get install -y --no-install-recommends certbot && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY docker/nginx.beta.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx.ssl.conf /etc/nginx/conf.d/ssl.conf

