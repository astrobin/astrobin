#!/bin/bash -ex

docker login --username ${DOCKER_USERNAME} --password ${DOCKER_PASSWORD}
docker pull ubuntu:16.04
docker build \
    -t astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION \
    -t $DOCKER_REGISTRY/astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION \
    -f docker/astrobin.dockerfile . &&
docker tag astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION $DOCKER_REGISTRY/astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION
