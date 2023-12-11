#!/bin/bash -ex

export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}
export ASTROBIN_HOST_TEMPORARY_FILES=/astrobin-temporary-files
export ASTROBIN_GUNICORN_WORKERS=1
export ARCH=$(uname -m)

export POSTGRES_PASSWORD="v3rys3cr3t"
export SUBNET_GROUP_NAME="default-vpc-b5c428ce"

compose="docker-compose \
    -f docker/docker-compose-app.yml \
    -f docker/docker-compose-worker.yml \
    -f docker/docker-compose-scheduler.yml \
    -f docker/docker-compose-local.yml"

if [ $"${ARCH}" == "aarch64" ]; then
    # https://docs.cypress.io/guides/getting-started/installing-cypress#Download-URLs
    echo "Skipping Cypress tests on aarch64 because Cypress does not support it yet."
    exit 0
fi

apt-get install -y ncat || exit 1

GET_POSTGRES_ENDPOINT="aws rds describe-db-instances --db-instance-identifier astrobin-test-${CODEBUILD_BUILD_NUMBER}"
JQ_GET_POSTGRES_ENDPOINT="jq -r ".DBInstances[0].Endpoint.Address""
POSTGRES_ENDPOINT="null"
while [[ "${POSTGRES_ENDPOINT}" == "null" ]]; do
    echo -n "Getting postgres endpoint... "
    POSTGRES_ENDPOINT=$(${GET_POSTGRES_ENDPOINT} | ${JQ_GET_POSTGRES_ENDPOINT})
    echo ${POSTGRES_ENDPOINT}
    sleep 5
done

export POSTGRES_HOST=${POSTGRES_ENDPOINT}

cat <<EOF > docker/astrobin.env
POSTGRES_HOST=${POSTGRES_HOST}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
EOF

until nc -zvw2 ${POSTGRES_ENDPOINT} 5432
do
    sleep 5
done

${compose} up &

sleep 30

${compose} stop postgres &

${compose} logs -f 2>&1 &

astrobin_attempts=0
astrobin_max_attempts=24
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://127.0.0.1:8083/account/login/)" != "200" ]]; do
    [[ $astrobin_attempts -eq $astrobin_max_attempts ]] && echo "Failed!" && exit 1
    echo "Waiting for astrobin (attempt ${astrobin_attempts})..."
    sleep 10
    astrobin_attempts=$((astrobin_attempts+1))
done

CYPRESS_baseUrl=http://127.0.0.1:8083 $(npm bin)/cypress run || exit 1

${compose} down || exit 1
