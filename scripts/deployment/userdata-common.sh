#!/bin/bash -ex

# Variables needed by this script:
#  - AWS_ACCESS_KEY_ID
#  - AWS_SECRET_ACCESS_KEY
#  - AWS_REGION
#  - RELEASE_TAG
#  - DOCKER_REGISTRY
#  - EFS_FILE_SYSTEM

# Assumptions:
#  - The astrobin repository is checked out at the root directory.

export DISPLAY=:0
export USER=ubuntu
export ASTROBIN_TEMPORARY_FILES=/astrobin-temporary-files
export USER=ubuntu
export GROUP=ubuntu

# Get initial packages:

apt-get update -y && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    awscli \
    binutils

# Get docker:

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
apt-cache policy docker-ce
apt-get install -y docker-ce
apt-get install -y docker-compose
usermod -aG docker ${USER}

# Get docker image:

aws configure set aws_access_key_id ${AWS_ACCESS_KEY_ID}
aws configure set aws_secret_access_key ${AWS_SECRET_ACCESS_KEY}
aws configure set aws_region ${AWS_REGION}
rm /usr/bin/docker-credential-secretservice
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${DOCKER_REGISTRY}
docker pull ${DOCKER_REGISTRY}/astrobin:${RELEASE_TAG}

# Install efs-utils:

git clone https://github.com/aws/efs-utils && (cd efs-utils && ./build-deb.sh && apt-get -y install ./build/amazon-efs-utils*deb)

# Mount EFS:

mkdir ${ASTROBIN_TEMPORARY_FILES}

tries=0
until [ "$tries" -ge 6 ]
do
   mount -t efs -o tls ${EFS_FILE_SYSTEM}:/ ${ASTROBIN_TEMPORARY_FILES} && break
   tries=$((tries+1))
   sleep 10
done

mkdir -p ${ASTROBIN_TEMPORARY_FILES}/files
chown ${USER}:${GROUP} ${ASTROBIN_TEMPORARY_FILES}/files
