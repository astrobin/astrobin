#!/bin/bash

BASEPATH=/var/www/astrobin_env
source $BASEPATH/bin/activate
python $BASEPATH/www/astrobin/manage.py update_index
deactivate

