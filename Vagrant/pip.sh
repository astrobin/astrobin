#!/bin/sh

# Init virtualenv
virtualenv --no-site-packages /venv/astrobin/dev
. /venv/astrobin/dev/bin/activate

# Install python requirements
pip install -r /var/www/astrobin/requirements.txt

# Install submodules
for d in /var/www/astrobin/submodules/*; do
    (
        cd $d;
        if [ -f setup.py ];
        then
            python setup.py install
        fi
    );
done

# TODO: No idea why...
(cd /venv/astrobin/dev/src/django-contrib-requestprovider/gadjolib/; python setup.py install)


