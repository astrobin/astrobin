#!/bin/bash -ex

RELEASE_TAG=${CODEBUILD_RESOLVED_SOURCE_VERSION}
AUTOSCALING_GROUP_NAME=$1
SLEEP_SECONDS=$2

AUTOSCALING_GROUP_DESCRIPTION=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names $AUTOSCALING_GROUP_NAME)
CURRENT_MIN_SIZE=$(echo "$AUTOSCALING_GROUP_DESCRIPTION" | jq -r ".AutoScalingGroups[0].MinSize")
CURRENT_MAX_SIZE=$(echo "$AUTOSCALING_GROUP_DESCRIPTION" | jq -r ".AutoScalingGroups[0].MaxSize")
CURRENT_DESIRED_CAPACITY=$(echo "$AUTOSCALING_GROUP_DESCRIPTION" | jq -r ".AutoScalingGroups[0].DesiredCapacity")

# Double up from the original numbers.

aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name ${AUTOSCALING_GROUP_NAME} \
    --min-size "$(($CURRENT_MIN_SIZE * 2))" \
    --max-size "$(($CURRENT_MAX_SIZE * 2))" \
    --desired-capacity "$(($CURRENT_DESIRED_CAPACITY * 2))"

sleep ${SLEEP_SECONDS}

# Finally return to the original numbers: now all instances have been replaced.

aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name ${AUTOSCALING_GROUP_NAME} \
    --min-size ${CURRENT_MIN_SIZE} \
    --max-size ${CURRENT_MAX_SIZE} \
    --desired-capacity ${CURRENT_DESIRED_CAPACITY}
