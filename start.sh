#!/bin/sh

PROJECT_DIR="/home/astrobin/Code/astrobin"
NGINX_PID="/usr/local/nginx/logs/nginx.pid"
ASTORBIN_PID="$PROJECT_DIR/astrobin.pid"

PREFIX=" > "

SUDO="sudo -E"
ECHO="echo ${PREFIX}"
ECHON="echo -n ${PREFIX}"
DONE="echo \"done.\""

if [ -e $NGINX_PID ]
then
    $ECHO 'nginx already running, skipping.'
else
    $ECHON 'Starting nginx... '
    $SUDO ./scripts/nginx.sh &
    $DONE
fi


if [ -e $NGINX_PID ]
then
    $ECHO 'astrobin already running, skipping.'
else
    $ECHON 'Starting astrobin... '
    ./scripts/gunicorn.sh &
    $DONE
fi

$ECHO 'All done.'

