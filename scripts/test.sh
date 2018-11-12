#!/bin/bash

coverage run --source=. ./manage.py test \
    astrobin astrobin_apps_groups \
    astrobin_apps_iotd \
    astrobin_apps_notifications \
    astrobin_apps_premium \
    rawdata \
    --noinput --failfast
