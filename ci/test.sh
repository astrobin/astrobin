#!/usr/bin/env bash

USE_SQLITE=true TESTING=true ./scripts/test.sh && (cd frontend && npm install && npm run ng -- test --code-coverage && npm run e2e)
