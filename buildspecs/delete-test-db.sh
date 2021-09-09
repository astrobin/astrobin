#!/bin/sh

aws rds delete-db-instance \
    --db-instance-identifier astrobin-test-${CODEBUILD_BUILD_NUMBER}
    --skip-final-snapshot \
    --delete-automated-backups
