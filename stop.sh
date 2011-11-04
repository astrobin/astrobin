#!/bin/sh
PROJECT_DIR="/home/astrobin/Code/astrobin"
NGINX_PID="/usr/local/nginx/logs/nginx.pid"
GUNICORN_PID="$PROJECT_DIR/astrobin.pid"
CELERYD_DEFAULT_PID="celeryd@default.pid"
CELERYD_PLATE_SOLVE_PID="celeryd@plate_solve.pid"

SUDO="sudo -E"
RM="rm -f"
ECHO="echo ${PREFIX}"
ECHON="echo -n ${PREFIX}"
DONE="echo done"
FAILED="(echo failed; exit 1;)"

if [ -e $NGINX_PID ]
then
    $ECHON 'Stopping nginx... '
    $SUDO kill `cat $NGINX_PID` 2>- && $RM $NGINX_PID
    $DONE
else
    $ECHO 'nginx not running.'
fi


if [ -e $GUNICORN_PID ]
then
    $ECHON 'Stopping gunicorn... '
    (kill `cat $GUNICORN_PID` 2>- && $RM $GUNICORN_PID) || $FAILED
    $DONE
else
    $ECHO 'gunicorn not running.'
fi

if [ -e $CELERYD_DEFAULT_PID ]
then
    $ECHON 'Stopping celeryd default worker... '
    ./manage.py celeryd_multi stop default $CELERYD_DEFAULT_PID 2>-|| $FAILED
    $DONE
else
    $ECHO 'celeryd default worker not running.'
fi

if [ -e $CELERYD_PLATE_SOLVE_PID ]
then
    $ECHON 'Stopping celeryd plate_solve worker... '
    ./manage.py celeryd_multi stop plate_solve $CELERYD_PLATE_SOLVE_PID 2>- || $FAILED
    $DONE
else
    $ECHO 'celeryd plate_solve worker not running.'
fi

$ECHO 'All done.'

