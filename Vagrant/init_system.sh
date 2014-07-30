#!/bin/sh

# Create directories
mkdir -p /webserver
mkdir -p /rawdata/files
mkdir -p /opt/solr
mkdir -p /venv
mkdir -p /var/www/astrobin/logs

groupadd -g 2000 astrobin

if ! id -u astrobin >/dev/null 2>&1; then
    useradd -MN -s /dev/null -g astrobin -u 2000 astrobin
fi

if ! id -u solr >/dev/null 2>&1; then
    useradd -MN -s /dev/null -g astrobin -u 2001 solr
fi

if id -u vagrant >/dev/null 2>&1; then
    usermod -G astrobin vagrant
fi

chown -R astrobin:astrobin /venv
chown -R astrobin:astrobin /webserver
chown -R astrobin:astrobin /rawdata
chown -R solr:astrobin /opt/solr

chmod g+w /venv
