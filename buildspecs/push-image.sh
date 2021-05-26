#!/bin/bash

aws ecr get-login-password --region us-east-1 | docker login \
    --username AWS \
    --password-stdin \
    $DOCKER_REGISTRY &&
docker push $DOCKER_REGISTRY/astrobin-nginx:$CODEBUILD_RESOLVED_SOURCE_VERSION &&
docker push $DOCKER_REGISTRY/astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION
