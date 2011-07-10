#!/bin/sh

NGINX_PID="/usr/local/nginx/logs/nginx.pid"

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

