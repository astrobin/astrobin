#!/bin/bash

export NGINX_MODE=dev
export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}

npm ci &
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.build.yml up -d &

while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost/accounts/login/)" != "200" ]]; do
    echo "Waiting for AstroBin..."
    sleep 5
done

$(npm bin)/cypress run
