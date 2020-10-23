#!/bin/bash -ex

# Variables needed by this script:
#  - EFS_FILE_SYSTEM

export ASTROBIN_BUILD=${RELEASE_TAG}
export ASTROBIN_TEMPORARY_FILES=/astrobin-temporary-files
export USER=ubuntu
export GROUP=ubuntu
export NGINX_MODE=prod


# Install efs-utils:

git clone https://github.com/aws/efs-utils && (cd efs-utils && ./build-deb.sh && apt-get -y install ./build/amazon-efs-utils*deb)

# Mount EFS:

mkdir ${ASTROBIN_TEMPORARY_FILES}
mount -t efs -o tls ${EFS_FILE_SYSTEM}:/ ${ASTROBIN_TEMPORARY_FILES}
mkdir -p ${ASTROBIN_TEMPORARY_FILES}/files
chown ${USER}:${GROUP} ${ASTROBIN_TEMPORARY_FILES}/files

# Create docker stack:

docker swarm init
docker stack deploy -c docker/docker-compose-app.yml app
