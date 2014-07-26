#!/bin/bash

cd /var/www/astrobin/submodules/astrobin/cfitsio
./configure
makea -j4

cd ..
qmake
make -j4

. /venv/astrobin/dev/bin/activate
make install
