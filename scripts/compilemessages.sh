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

cd astrobin_apps_users
django-admin.py compilemessages
cd ..

cd astrobin_apps_platesolving
django-admin.py compilemessages
cd ..

cd astrobin_apps_images
django-admin.py compilemessages
cd ..
