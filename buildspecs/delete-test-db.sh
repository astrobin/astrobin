#!/bin/sh

export ARCH=$(uname -m)

if [ $ARCH == "aarch64" ]; then
    # https://docs.cypress.io/guides/getting-started/installing-cypress#Download-URLs
    echo "Skipping this step on aarch64 because we're not running Cypress tests there."
    exit 0
fi

aws rds delete-db-instance \
    --db-instance-identifier astrobin-test-${CODEBUILD_BUILD_NUMBER} \
    --skip-final-snapshot \
    --delete-automated-backups
