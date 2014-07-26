#!/bin/sh

# Create directories
mkdir -p /webserver
mkdir -p /rawdata/files
mkdir -p /venv
mkdir -p /var/www/astrobin/logs

chown vagrant:vagrant /venv
chown vagrant:vagrant /webserver
chown vagrant:vagrant /rawdata
