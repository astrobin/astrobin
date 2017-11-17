#!/bin/sh

lessc astrobin/static/css/astrobin.less > astrobin/static/css/astrobin.css
lessc astrobin/static/css/astrobin-mobile.less > astrobin/static/css/astrobin-mobile.css
./manage.py collectstatic --noinput
echo 'flush_all' | netcat localhost 11211

