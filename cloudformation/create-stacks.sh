#!/usr/bin/env bash

REGION=$1
CERTIFICATE_ARN=$2

PREFIX=$(cat ./stack-prefix.txt)
CF="aws --region ${REGION} cloudformation"

for STACK_FILE in $(find ./sequential -name '*.yml' | sort | xargs)
do
    STACK_NAME=$(basename ${STACK_FILE%.*})
    PARAMS=()

    if [[ $STACK_NAME == "01-secret-parameter-store" ]]; then
        PARAMS+=(--parameters file:///${PWD}/beta-secret-parameters.env.json)
    fi

    echo Crating stack ${PREFIX}-${STACK_NAME}...
    ${CF} create-stack \
        --stack-name ${PREFIX}-${STACK_NAME} \
        --template-body file://${PWD}/${STACK_FILE} \
        "${PARAMS[@]}" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM >/dev/null && \
    ${CF} wait stack-create-complete --stack-name ${PREFIX}-${STACK_NAME} >/dev/null || exit 1
done

for STACK_FILE in $(find ./parallel -name '*.yml' | sort | xargs)
do
    STACK_NAME=$(basename ${STACK_FILE%.*})
    PARAMS=()

    if [[ $STACK_NAME == "15-astrobin-app-service" ]]; then
        PARAMS+=(--parameters ParameterKey=CertificateArnParameter,ParameterValue=${CERTIFICATE_ARN})
    fi

    echo Crating stack ${PREFIX}-${STACK_NAME}...
    ${CF} create-stack \
        --stack-name ${PREFIX}-${STACK_NAME} \
        --template-body file://${PWD}/${STACK_FILE} \
        "${PARAMS[@]}" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM >/dev/null
done

for STACK_FILE in $(find ./parallel -name '*.yml' | sort | xargs)
do
    STACK_NAME=$(basename ${STACK_FILE%.*})
    ${CF} wait stack-create-complete --stack-name ${PREFIX}-${STACK_NAME} >/dev/null || exit 1
done
