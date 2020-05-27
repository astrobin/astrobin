#!/usr/bin/env bash

python manage.py sync_translation_fields --noinput
USE_SQLITE=true TESTING=true ./scripts/test.sh
