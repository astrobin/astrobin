#!/bin/sh

# Initialize the environment
. /venv/astrobin/dev/bin/activate
. /var/www/astrobin/env/dev

# Initialize db
/var/www/astrobin/manage.py syncdb --noinput
/var/www/astrobin/manage.py migrate
/var/www/astrobin/manage.py collectstatic --noinput
