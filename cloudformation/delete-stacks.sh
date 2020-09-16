#!/usr/bin/env bash

REGION=$(cat ./region.txt)
PREFIX=$(cat ./stack-prefix.txt)
CF="aws --region ${REGION} cloudformation"

for STACK_FILE in $(find ./parallel -name '*.yml' | sort -r | xargs)
do
    STACK_NAME=$(basename ${STACK_FILE%.*})
    echo Deleting ${PREFIX}-${STACK_NAME}...
    ${CF} delete-stack --stack-name ${PREFIX}-${STACK_NAME} >/dev/null && \
    ${CF} wait stack-delete-complete --stack-name ${PREFIX}-${STACK_NAME} >/dev/null || exit 1
done

for STACK_FILE in $(find ./sequential -name '*.yml' | sort -r | xargs)
do
    STACK_NAME=$(basename ${STACK_FILE%.*})
    echo Deleting ${PREFIX}-${STACK_NAME}...
    ${CF} delete-stack --stack-name ${PREFIX}-${STACK_NAME} >/dev/null && \
    ${CF} wait stack-delete-complete --stack-name ${PREFIX}-${STACK_NAME} >/dev/null || exit 1
done
