#!/bin/bash

coverage run --source=. ./manage.py test \
    astrobin astrobin_apps_groups \
    astrobin_apps_iotd \
    astrobin_apps_notifications \
    astrobin_apps_premium \
    rawdata \
    --noinput --failfast

if [ $? -eq 0 ]; then
    if [[ -z "${CODECOV_TOKEN}" ]]; then
        echo "Please export CODECOV_TOKEN to upload coverage results to Codecov"
        exit 0
    else
        codecov -t ${CODECOV_TOKEN}
    fi
else
    exit $?
fi
