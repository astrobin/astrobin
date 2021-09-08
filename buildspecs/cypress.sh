#!/bin/bash -ex

export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}
export ASTROBIN_GUNICORN_WORKERS=1
export ARCH=$(uname -m)

compose="docker-compose \
    -f docker/docker-compose-app.yml \
    -f docker/docker-compose-worker.yml \
    -f docker/docker-compose-scheduler.yml \
    -f docker/docker-compose-local.yml \
    up"

if [ $ARCH == "aarch64" ]; then
    # https://docs.cypress.io/guides/getting-started/installing-cypress#Download-URLs
    echo "Skipping Cypress tests on aarch64 because Cypress does not support it yet."
    exit 0
fi

docker login --username ${DOCKER_USERNAME} --password ${DOCKER_PASSWORD} || exit 1

npm ci || exit 2

${compose} up &

sleep 30

${compose} logs -f 2>&1 &

astrobin_attempts=0
astrobin_max_attempts=24
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://127.0.0.1:8083/accounts/login/)" != "200" ]]; do
    [[ $astrobin_attempts -eq $astrobin_max_attempts ]] && echo "Failed!" && exit 3
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
    [[ $astrobin_ng_attempts -eq $astrobin_ng_max_attempts  ]] && echo "Failed!" && exit 4
    echo "Waiting for astrobin-ng..."
    sleep 5
    ((astrobin_ng_attempts++))
done

CYPRESS_baseUrl=http://127.0.0.1:8083 $(npm bin)/cypress run || exit 5

compose down || exit 6
