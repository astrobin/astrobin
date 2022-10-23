#!/bin/sh

export CONTAINER=docker-astrobin-1

docker exec -it $CONTAINER scss astrobin/static/astrobin/scss/astrobin.scss > astrobin/static/astrobin/scss/astrobin.css
docker cp astrobin/static/astrobin/scss/astrobin.css $CONTAINER:/code/astrobin/static/astrobin/scss
docker exec -it $CONTAINER ./manage.py collectstatic --no-input
