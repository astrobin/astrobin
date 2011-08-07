#! /bin/sh
if [ -e data/cities.txt.gz ]; then
    if [ ! -e data/cities.txt ]; then
        gunzip data/cities.txt.gz
    fi
fi
./manage.py create_cities_db
