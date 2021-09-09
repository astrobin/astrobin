#!/bin/sh

ARCH=$(uname -m)

if [ $ARCH == "aarch64" ]; then
    # https://docs.cypress.io/guides/getting-started/installing-cypress#Download-URLs
    echo "Skipping this step on aarch64 because we're not running Cypress tests there."
    exit 0
fi

POSTGRES_PASSWORD="v3rys3cr3t"
SUBNET_GROUP_NAME="default-vpc-b5c428ce"

aws rds create-db-instance \
    --db-name astrobin \
    --db-instance-identifier astrobin-test-${CODEBUILD_BUILD_NUMBER} \
    --allocated-storage 100 \
    --engine postgres \
    --db-instance-class db.r5.large \
    --master-username astrobin \
    --master-user-password ${POSTGRES_PASSWORD} \
    --availability-zone us-east-1a \
    --no-multi-az \
    --publicly-accessible \
    --no-deletion-protection \
    --db-subnet-group-name ${SUBNET_GROUP_NAME}
