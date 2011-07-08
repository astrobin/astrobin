#! /bin/sh
./venv/bin/python manage.py celerybeat --verbosity=2 --loglevel=DEBUG
