#!/bin/bash

export NGINX_MODE=dev
export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}

npm ci &
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.build.yml up -d &
sleep 300
$(npm bin)/cypress run
