#!/bin/bash
# vim: syntax=sh ts=4 sts=4 sw=4 expandtab

PATH=/usr/local/bin:/usr/bin:/bin

if [ ! -f docker/docker-compose.yml ]; then
    echo "ERROR: Run this script from the root of the git repository."
    exit 1
fi

cat <<EOF
**********************************************************
*** DANGER *** DANGER *** DANGER *** DANGER *** DANGER ***
**********************************************************

Executing this script will reset your local development
build back to scratch.  It will:

 * Shutdown your currently running development environment (if any)
 * Delete all AstroBin Docker volumes
 * Delete all of the built Docker container images

You should only proceed if you are SURE you want to start
over from scratch.

EOF

echo -n "Proceed? "
read yn
case $yn in
    y*|Y*) : ;;
    *)
        echo "Aborting!"
        exit 1
        ;;
esac

echo "Shutting down the development stack..."
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.build.yml down

echo "Removing data volumes..."
docker volume rm docker_media
docker volume rm docker_postgres-data
docker volume rm docker_elasticsearch-data
docker volume rm docker_letsencrypt

echo "Removing container images..."
for image in astrobin/nginx-dev astrobin/astrobin; do
    echo "-- $image"
    docker image rm $(docker image ls | grep $image | awk '{print $3}')
done
