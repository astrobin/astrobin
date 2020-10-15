#!/bin/bash

docker run astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION bash -c "\
    ./scripts/test.sh && \
    coverage xml && \
    codecov --commit=$CODEBUILD_RESOLVED_SOURCE_VERSION -t $CODECOV_TOKEN"
