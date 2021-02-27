#!/bin/bash -ex

export NGINX_MODE=dev
export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}
export ASTROBIN_GUNICORN_WORKERS=1

npm ci &
docker-compose \
   -f docker/docker-compose-app.yml \
   -f docker/docker-compose-worker.yml \
   -f docker/docker-compose-scheduler.yml \
   -f docker/docker-compose-local.yml \
   up -d &

(\
    cd ..;\
    git clone https://github.com/astrobin/astrobin-ng.git && cd astrobin-ng;
    npm ci && \
    npm start
)

while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost/accounts/login/)" != "200" ]]; do
    echo "Waiting for AstroBin..."
    sleep 5
done

while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:4400/account/login)" != "200" ]]; do
    echo "Waiting for AstroBin NG..."
    sleep 5
done

$(npm bin)/cypress run
