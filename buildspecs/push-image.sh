#!/bin/bash

docker tag astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION $ECR_URL/astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION &&
aws ecr get-login-password --region us-east-1 | docker login \
    --username AWS \
    --password-stdin \
    $ECR_URL &&
docker push $ECR_URL/astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION
