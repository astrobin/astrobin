#!/bin/sh

lessc astrobin/static/css/astrobin.less > astrobin/static/css/astrobin.css
./manage.py collectstatic --noinput
echo 'flush_all' | netcat localhost 11211

