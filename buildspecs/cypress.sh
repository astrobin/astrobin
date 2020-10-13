#!/bin/bash

export NGINX_MODE=dev
export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}

docker-compose -f docker/docker-compose.yml -f docker/docker-compose.build.yml up -d &
sleep 300
npm ci && CYPRESS_baseUrl=http://localhost $(npm bin)/cypress run
