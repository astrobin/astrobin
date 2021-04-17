#!/bin/bash

export USE_SQLITE=true
export TESTING=true

coverage run \
    --source=. \
    ./manage.py test \
        --noinput \
        --failfast \
        --verbosity=2 \
        astrobin.tests.test_moderation.ModerationTest
