#!/bin/bash
cd astrobin; django-admin.py makemessages -a -e html,txt,py -i *zinnia*; cd ..
cd rawdata; django-admin.py makemessages -a; cd ..
cd nested_comments; django-admin.py makemessages -a; cd ..
