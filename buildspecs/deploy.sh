#!/bin/bash

RELEASE_TAG=${CODEBUILD_RESOLVED_SOURCE_VERSION}
TEMPLATE_NAME=$1
AUTOSCALING_GROUP_NAME=$2
SLEEP_SECONDS=$3

TEMPLATE=$(aws ec2 describe-launch-template-versions --launch-template-name ${TEMPLATE_NAME} --max-items 1)
VERSION_NUMBER=$(echo "${TEMPLATE}" | jq -r '.LaunchTemplateVersions[0].VersionNumber')
USER_DATA=$(echo "${TEMPLATE}" | jq -r '.LaunchTemplateVersions[0].LaunchTemplateData.UserData' | base64 -d)
UPDATED_USER_DATA=$(echo "$USER_DATA" | sed -E 's/export RELEASE_TAG=([a-fA-F0-9]{40})/export RELEASE_TAG='${RELEASE_TAG}'/' | base64 -w 0)
NEW_TEMPLATE_VERSION=$(aws ec2 create-launch-template-version \
    --launch-template-name ${TEMPLATE_NAME} \
    --source-version ${VERSION_NUMBER} \
    --version-description $(date +"%Y-%m-%d")-${RELEASE_TAG} \
    --launch-template-data '{"UserData": "'${UPDATED_USER_DATA}'"}'
)
NEW_VERSION_NUMBER=$(echo "${NEW_TEMPLATE_VERSION}" | jq -r '.LaunchTemplateVersion.VersionNumber')
MODIFIED_DEFAULT_VERSION=$(aws ec2 modify-launch-template \
    --launch-template-name ${TEMPLATE_NAME} \
    --default-version ${NEW_VERSION_NUMBER}
)
AUTOSCALING_GROUP_DESCRIPTION=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names astrobin-autoscaling-group)
CURRENT_MIN_SIZE=$(echo "$AUTOSCALING_GROUP_DESCRIPTION" | jq -r ".AutoScalingGroups[0].MinSize")
CURRENT_MAX_SIZE=$(echo "$AUTOSCALING_GROUP_DESCRIPTION" | jq -r ".AutoScalingGroups[0].MaxSize")
CURRENT_DESIRED_CAPACITY=$(echo "$AUTOSCALING_GROUP_DESCRIPTION" | jq -r ".AutoScalingGroups[0].DesiredCapacity")

aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name ${AUTOSCALING_GROUP_NAME} \
    --min-size "$(($CURRENT_MIN_SIZE * 2))" \
    --max-size "$(($CURRENT_MAX_SIZE * 2))" \
    --desired-capacity "$(($CURRENT_DESIRED_CAPACITY * 2))"

sleep ${SLEEP_SECONDS}

aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name ${AUTOSCALING_GROUP_NAME} \
    --min-size ${CURRENT_MIN_SIZE} \
    --max-size ${CURRENT_MAX_SIZE} \
    --desired-capacity ${CURRENT_DESIRED_CAPACITY}
