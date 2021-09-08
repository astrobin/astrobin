#!/bin/bash -ex

export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}
export ASTROBIN_GUNICORN_WORKERS=1
export ARCH=$(uname -m)

export TIMESTAMP=$(date +"%s")
export POSTGRES_PASSWORD="v3rys3cr3t"
export SUBNET_GROUP_NAME="default-vpc-b5c428ce"

compose="docker-compose \
    -f docker/docker-compose-app.yml \
    -f docker/docker-compose-worker.yml \
    -f docker/docker-compose-scheduler.yml \
    -f docker/docker-compose-local.yml"

if [ $ARCH == "aarch64" ]; then
    # https://docs.cypress.io/guides/getting-started/installing-cypress#Download-URLs
    echo "Skipping Cypress tests on aarch64 because Cypress does not support it yet."
    exit 0
fi

docker login --username ${DOCKER_USERNAME} --password ${DOCKER_PASSWORD} || exit 1

npm ci || exit 1

aws rds create-db-instance \
    --db-name astrobin \
    --db-instance-identifier astrobin-test-${TIMESTAMP} \
    --allocated-storage 100 \
    --engine postgres \
    --db-instance-class db.r5.large \
    --master-username astrobin \
    --master-user-password ${POSTGRES_PASSWORD} \
    --availability-zone us-east-1a \
    --no-multi-az \
    --publicly-accessible \
    --no-deletion-protection \
    --db-subnet-group-name ${SUBNET_GROUP_NAME} 2>&1 >/dev/null || exit 1

GET_POSTGRES_HOST="aws rds describe-db-instances --db-instance-identifier astrobin-test-${TIMESTAMP}"
JQ_GET_POSTGRES_HOST="jq -r ".DBInstances[0].Endpoint.Address""
POSTGRES_HOST="null"
while [[ "${POSTGRES_HOST}" == "null" ]]; do
    echo -n "Getting postgres host... "
    POSTGRES_HOST=$(${GET_POSTGRES_HOST} | ${JQ_GET_POSTGRES_HOST})
    echo ${POSTGRES_HOST}
    sleep 5
done

# Wait for two minutes for postgres to be up.
nc -zvw120 ${POSTGRES_HOST} 5432 || exit 1

${compose} up &

sleep 30

${compose} logs -f 2>&1 &

astrobin_attempts=0
astrobin_max_attempts=24
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://127.0.0.1:8083/accounts/login/)" != "200" ]]; do
    [[ $astrobin_attempts -eq $astrobin_max_attempts ]] && echo "Failed!" && exit 1
    echo "Waiting for astrobin..."
    sleep 5
    ((astrobin_attempts++))
done

(
    git clone https://github.com/astrobin/astrobin-ng.git &&
    cd astrobin-ng &&
    npm ci &&
    npm run start:cypress
) &

astrobin_ng_attempts=0
astrobin_ng_max_attempts=24
while [[ "$(curl -s -o /dev/null http://127.0.0.1:4400)" ]]; do
    [[ $astrobin_ng_attempts -eq $astrobin_ng_max_attempts  ]] && echo "Failed!" && exit 1
    echo "Waiting for astrobin-ng..."
    sleep 5
    ((astrobin_ng_attempts++))
done

CYPRESS_baseUrl=http://127.0.0.1:8083 $(npm bin)/cypress run || exit 1

compose down || exit 1

aws rds delete-db-instance \
    --db-instance-identifier astrobin-test-${TIMESTAMP}
    --skip-final-snapshot \
    --delete-automated-backups 2>&1 >/dev/null || exit 1
