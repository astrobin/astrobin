#! /bin/sh
./manage.py celeryd -Q default -c 4 -E --pidfile=celeryd@default.pid --logfile=celeryd@default.log
