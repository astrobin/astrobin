#!/bin/bash
coverage run --source=. ./manage.py test --noinput --failfast
