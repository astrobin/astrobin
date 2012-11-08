#!/bin/bash
cd astrobin
~/venv/production/bin/django-admin.py makemessages -a -e html,txt,py -i *zinnia*
