#!/bin/bash -ex

export NGINX_MODE=dev
export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}

npm ci &
docker-compose \
   -f docker/docker-compose-app.yml \
   -f docker/docker-compose-worker.yml \
   -f docker/docker-compose-scheduler.yml \
   -f docker/docker-compose-local.yml \
   up -d &

while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost/accounts/login/)" != "200" ]]; do
    echo "Waiting for AstroBin..."
    sleep 5
done

$(npm bin)/cypress run
