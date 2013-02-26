#!/bin/bash
cd astrobin
django-admin.py compilemessages
cd ..

cd nested_comments
django-admin.py compilemessages
cd ..

cd rawdata
django-admin.py compilemessages
cd ..
