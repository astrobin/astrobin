#!/bin/bash

if [ ! -f /opt/solr/solr.tgz ]; then
sudo -u solr /bin/bash - <<"EOF"
curl https://archive.apache.org/dist/lucene/solr/4.4.0/solr-4.4.0.tgz > /opt/solr/solr.tgz
tar xvfz /opt/solr/solr.tgz -C /opt/solr
chmod g+w /opt/solr/ -R
EOF
fi

sudo -u astrobin /bin/bash - <<"EOF"
. /venv/astrobin/dev/bin/activate
. /var/www/astrobin/env/dev

/var/www/astrobin/manage.py build_solr_schema > /opt/solr/solr-4.4.0/example/solr/collection1/conf/schema.xml
EOF
