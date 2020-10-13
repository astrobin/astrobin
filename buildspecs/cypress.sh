#!/bin/bash

export NGINX_MODE=dev
export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}

exec 3< <(docker-compose -f docker/docker-compose.yml -f docker/docker-compose.build.yml up) &&
sed '/[INFO] Listening at/q' <&3 &&
npm ci && CYPRESS_baseUrl=http://localhost $(npm bin)/cypress run
