#!/bin/sh

# Create directories
mkdir -p /var/www/media
mkdir -p /rawdata/files
mkdir -p /opt/solr
mkdir -p /venv
mkdir -p /var/log/astrobin

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
chown -R astrobin:astrobin /var/www/media
chown -R astrobin:astrobin /rawdata
chown -R solr:astrobin /opt/solr
chown -R astrobin:astrobin /var/log/astrobin

chmod g+w /venv
chmod g+w /var/www/media
chmod g+w /rawdata
chmod g+w /opt/solr
chmod g+w /var/log/astrobin
