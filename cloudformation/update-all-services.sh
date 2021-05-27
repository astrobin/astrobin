#!/usr/bin/env bash

set -x

REGION=$1

SERVICES=`aws --region ${REGION} ecs list-services --cluster astrobin-cluster --output text | awk -F ' ' '{print $2}'`

for SERVICE in ${SERVICES}
do
    aws --region ${REGION} ecs update-service --force-new-deployment --cluster astrobin-cluster --service ${SERVICE}
done
