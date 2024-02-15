#!/bin/bash -ex

export CORES=$(grep -c processor /proc/cpuinfo)
export ASTROBIN_GUNICORN_WORKERS=$((2 * CORES + 1))
export ASTROBIN_BUILD=${RELEASE_TAG}

# Create docker stack:

docker swarm init
docker stack deploy -c docker/docker-compose-app.yml app
