#!/bin/sh

PROJECT_DIR="/home/astrobin/Code/astrobin"
NGINX_PID="/usr/local/nginx/logs/nginx.pid"
GUNICORN_PID="$PROJECT_DIR/astrobin.pid"
CELERYD_DEFAULT_PID="celeryd_default.pid"
CELERYD_PLATE_SOLVE_PID="celeryd_plate_solve.pid"

SUDO="sudo -E"
ECHO="echo ${PREFIX}"
ECHON="echo -n ${PREFIX}"
DONE="echo done"
FAILED="(echo failed; exit 1;)"

if [ -e $NGINX_PID ]
then
    $ECHO 'nginx already running, skipping.'
else
    $ECHON 'Starting nginx... '
    $SUDO ./scripts/nginx.sh
    $DONE
fi


if [ -e $GUNICORN_PID ]
then
    $ECHO 'astrobin already running, skipping.'
else
    $ECHON 'Starting astrobin... '
    ./scripts/gunicorn.sh &
    $DONE
fi

if [ -e $CELERYD_DEFAULT_PID ]
then
    $ECHO 'celeryd default worker already running, skipping.'
else
    $ECHON 'Starting celeryd default worker... '
    ./scripts/celeryd_default.sh
    $DONE
fi

if [ -e $CELERYD_PLATE_SOLVE_PID ]
then
    $ECHO 'celeryd plate_solve worker already running, skipping.'
else
    $ECHON 'Starting celeryd plate_solve worker... '
    ./scripts/celeryd_plate_solve.sh
    $DONE
fi

$ECHO 'All done.'

