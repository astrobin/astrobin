#!/bin/bash

set -x

docker network create test-network

docker run \
    --network test-network \
    --network-alias postgres \
    --name postgres \
    -e POSTGRES_USER=astrobin \
    -e POSTGRES_PASSWORD=astrobin \
    -e POSTGRES_DB=astrobin \
    -d \
    postgres:10

docker run --network test-network astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION bash -c "\
    ./scripts/test.sh && \
    coverage xml && \
    curl -s https://codecov.io/bash | bash -s - -C $CODEBUILD_RESOLVED_SOURCE_VERSION -t ${CODECOV_TOKEN}"

docker kill postgres
docker rm postgres
docker network rm test-network
