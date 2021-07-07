#!/bin/bash -ex

export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}
export ASTROBIN_GUNICORN_WORKERS=1
export ARCH=$(uname -m)
export USER=ubuntu

if [ "$ARCH" == "aarch64" ]; then
    UBUNTU_ARCH=arm64
else
    UBUNTU_ARCH=amd64
fi

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=${UBUNTU_ARCH}] https://download.docker.com/linux/ubuntu focal stable"
apt-cache policy docker-ce
apt-get install -y docker-ce
apt-get install -y docker-compose
usermod -aG docker ${USER}

docker --version
docker-compose --version
