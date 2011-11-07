#! /bin/sh
./manage.py celeryd -Q default -c 4 -E --pidfile=celeryd_default.pid --logfile=celeryd_default.log
