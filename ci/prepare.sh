#!/usr/bin/env bash

sudo ln -s /usr/lib/x86_64-linux-gnu/libraw.so /usr/lib/x86_64-linux-gnu/libraw.so.10
sudo mkdir /media/{images,static} && sudo chmod 777 /media/{images,static}
./manage.py collectstatic --noinput --verbosity 0
