#!/bin/bash -ex

export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}
export ASTROBIN_HOST_TEMPORARY_FILES=/astrobin-temporary-files
export ASTROBIN_GUNICORN_WORKERS=1
export ARCH=$(uname -m)
export USER=$(whoami)

if [ "$ARCH" == "x86_64" ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
    apt-get update
    apt-cache policy docker-ce
    apt-get install -y docker-ce
    apt-get install -y docker-compose
    usermod -aG docker ${USER}
fi

docker --version
docker-compose --version
