#!/bin/bash

coverage run ./manage.py test \
    astrobin astrobin_apps_groups astrobin_apps_notifications \
    astrobin_apps_premium rawdata \
    --noinput --failfast
if [ ${PIPESTATUS[0]} -eq 0 ]
then
    echo -n "Counting asserts... "
    echo "~$(git grep "self.*assert" | wc -l)"

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
