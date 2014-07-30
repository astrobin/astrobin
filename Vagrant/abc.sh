#!/bin/bash

. /venv/astrobin/dev/bin/activate

cd /var/www/astrobin/submodules/abc/cfitsio
./configure
make -j4

cd ..
qmake
make -j4

make install
