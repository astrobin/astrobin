#!/bin/bash -ex

export ASTROBIN_BUILD=${CODEBUILD_RESOLVED_SOURCE_VERSION}
export ASTROBIN_GUNICORN_WORKERS=1
export ARCH=$(uname -m)

if [ $ARCH == "aarch64" ]; then
    # https://docs.cypress.io/guides/getting-started/installing-cypress#Download-URLs
    echo "Skipping Cypress tests on aarch64 because Cypress does not support it yet."
    exit 0
fi

npm ci &
docker-compose \
   -f docker/docker-compose-app.yml \
   -f docker/docker-compose-worker.yml \
   -f docker/docker-compose-scheduler.yml \
   -f docker/docker-compose-local.yml \
   up -d &


while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://127.0.0.1:8083/accounts/login/)" != "200" ]]; do
    echo "Waiting for astrobin..."
    sleep 5
done

(
    git clone https://github.com/astrobin/astrobin-ng.git &&
    cd astrobin-ng &&
    npm ci &&
    npm run start:cypress
) &

while [[ "$(curl -s -o /dev/null http://127.0.0.1:4400)" ]]; do
    echo "Waiting for astrobin-ng..."
    sleep 5
done

CYPRESS_baseUrl=http://127.0.0.1:8083 $(npm bin)/cypress run
