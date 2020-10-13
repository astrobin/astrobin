#!/bin/bash

docker build -t astrobin:$CODEBUILD_RESOLVED_SOURCE_VERSION -f docker/astrobin.dockerfile .
