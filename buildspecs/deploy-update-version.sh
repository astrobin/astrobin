#!/bin/bash -ex

RELEASE_TAG=${CODEBUILD_RESOLVED_SOURCE_VERSION}
TEMPLATE_NAME=$1

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
