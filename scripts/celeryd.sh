#! /bin/sh
./manage.py celeryd -E --verbosity=2 --loglevel=DEBUG -c 4 --queues=default &
./manage.py celeryd -E --verbosity=2 --loglevel=DEBUG -c 1 --queues=plate_solve &
