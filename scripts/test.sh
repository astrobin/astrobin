#!/bin/bash
coverage run ./manage.py test astrobin &&\
coverage report --omit="/venv/*" &&\
coverage html --omit="/venv/*" -d cover
