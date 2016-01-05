#!/bin/bash

echo "Running tests..."
coverage run ./manage.py test astrobin rawdata --noinput --failfast
if [ ${PIPESTATUS[0]} -eq 0 ]
then
    echo -n "Generating HTML report... "
    coverage html --omit="/venv/*" -d cover >/dev/null 2>&1 && echo "OK"

    echo -n "Total coverage: "
    coverage report --omit="/venv/*" |& grep "TOTAL" | awk '{print $4}'

    echo
    echo "--------------------------------------------"
    echo "See full coverage report at cover/index.html"
    echo "All done. Thanks for testing!"
    echo "--------------------------------------------"
fi
