#!/bin/bash -ex

export ARCH=$(uname -m)

aws ecr get-login-password --region us-east-1 | docker login \
    --username AWS \
    --password-stdin \
    $DOCKER_REGISTRY &&
docker pull $DOCKER_REGISTRY/astrobin-${ARCH}:$CODEBUILD_RESOLVED_SOURCE_VERSION
