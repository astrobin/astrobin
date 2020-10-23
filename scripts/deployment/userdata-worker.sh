#!/bin/bash -ex

docker swarm init
docker stack deploy -c docker/docker-compose-worker.yml worker
