#!/bin/bash

cd /var/www/astrobin/submodules/abc/cfitsio
./configure
make -j4

cd ..
qmake
make -j4

. /venv/astrobin/dev/bin/activate
make install
