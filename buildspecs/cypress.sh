#!/bin/bash

export NGINX_MODE=dev
export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}

exec 3< <(docker-compose -f docker/docker-compose.yml -f docker/docker-compose.build.yml up) &&
sed '/[INFO] Listening at/q' <&3 &&
docker exec -t docker_astrobin_1 bash -c "npm ci && CYPRESS_baseUrl=http://localhost:8083 $(npm bin)/cypress run"
