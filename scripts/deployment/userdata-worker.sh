#!/bin/bash -ex

export ASTROBIN_BUILD=${RELEASE_TAG}

docker swarm init
docker stack deploy -c docker/docker-compose-worker.yml worker
