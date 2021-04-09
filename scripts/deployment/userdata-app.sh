#!/bin/bash -ex

export CORES=$(cat /proc/cpuinfo | grep processor | wc -l)
export ASTROBIN_GUNICORN_WORKERS=$((++CORES))
export ASTROBIN_BUILD=${RELEASE_TAG}
export NGINX_MODE=prod

# Create docker stack:

docker swarm init
docker stack deploy -c docker/docker-compose-app.yml app
