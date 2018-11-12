#!/bin/bash

if [[ -z "${CODECOV_TOKEN}" ]]; then
    echo "Please export CODECOV_TOKEN to upload coverage results to Codecov"
    exit 0
else
    codecov -t ${CODECOV_TOKEN}
fi
