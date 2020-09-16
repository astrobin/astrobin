#!/usr/bin/env bash

PREFIX=$(cat ./stack-prefix.txt)
CF="aws --region ${REGION} cloudformation"
REGION=$1

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
