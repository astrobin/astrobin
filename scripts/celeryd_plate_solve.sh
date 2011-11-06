#! /bin/sh
./manage.py celeryd -Q plate_solve -c 1 -E --pidfile=celeryd@plate_solve.pid --logfile=celeryd@plate_solve.log
