#! /bin/sh
./manage.py celeryd -Q plate_solve -c 1 -E --pidfile=celeryd_plate_solve.pid --logfile=celeryd_plate_solve.log
