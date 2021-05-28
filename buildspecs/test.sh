#!/bin/bash -ex

export ARCH=$(uname -m)

docker run astrobin-${ARCH}:$CODEBUILD_RESOLVED_SOURCE_VERSION bash -c "\
    ./scripts/test.sh && \
    coverage xml && \
    curl -s https://codecov.io/bash | bash -s - -C $CODEBUILD_RESOLVED_SOURCE_VERSION -t ${CODECOV_TOKEN}"
