#!/bin/bash

docker build -t astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION -f docker/astrobin.dockerfile . &&
docker tag astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION $DOCKER_REGISTRY/astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION
