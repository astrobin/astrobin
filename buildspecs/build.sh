#!/bin/bash -ex

export ARCH=$(uname -m)

docker login --username ${DOCKER_USERNAME} --password ${DOCKER_PASSWORD} || exit 1

docker pull ubuntu:16.04 || exit 1

docker build \
    -t astrobin-${ARCH}:$CODEBUILD_RESOLVED_SOURCE_VERSION \
    -t $DOCKER_REGISTRY/astrobin-${ARCH}:$CODEBUILD_RESOLVED_SOURCE_VERSION \
    -f docker/astrobin.dockerfile . || exit 1

docker tag \
    astrobin-${ARCH}:$CODEBUILD_RESOLVED_SOURCE_VERSION \
    $DOCKER_REGISTRY/astrobin-${ARCH}:$CODEBUILD_RESOLVED_SOURCE_VERSION || exit 1
