#!/bin/bash

export TESTING=true

coverage run --source=. ./manage.py test --noinput --verbosity=2
