#! /bin/sh
./manage.py celeryd -E --verbosity=2 --loglevel=DEBUG -c 4
