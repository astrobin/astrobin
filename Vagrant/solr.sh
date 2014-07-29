#!/bin/bash

SOLR_DIR=/opt/solr
SOLR_ARCHIVE=$SOLR_DIR/solr.tgz
SOLR_SCHEMA=$SOLR_DIR/solr-4.4.0/example/solr/collection1/conf/schema.xml

if [ ! -f $SOLR_ARCHIVE ]; then
    curl https://archive.apache.org/dist/lucene/solr/4.4.0/solr-4.4.0.tgz > $SOLR_ARCHIVE
    tar xvfz $SOLR_ARCHIVE -C $SOLR_DIR
fi

sudo -u solr chmod g+w $SOLR_SCHEMA

sudo -u astrobin /bin/bash - <<"EOF"
. /venv/astrobin/dev/bin/activate
. /var/www/astrobin/env/dev

/var/www/astrobin/manage.py build_solr_schema > /opt/solr/solr-4.4.0/example/solr/collection1/conf/schema.xml
EOF
