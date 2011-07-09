#! /bin/sh
./manage.py run_gunicorn 0.0.0.0:8082 -w 1
