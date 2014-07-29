#!/bin/sh

# Create directories
mkdir -p /webserver
mkdir -p /rawdata/files
mkdir -p /opt/solr
mkdir -p /venv
mkdir -p /var/www/astrobin/logs

groupadd astrobin

if ! id -u astrobin >/dev/null 2>&1; then
    useradd -MN -s /dev/null -g astrobin astrobin
fi

if ! id -u solr >/dev/null 2>&1; then
    useradd -MN -s /dev/null -g astrobin solr
fi

chown -R astrobin:astrobin /venv
chown -R astrobin:astrobin /webserver
chown -R astrobin:astrobin /rawdata
chown -R solr:astrobin /opt/solr

