#!/bin/bash

if [ ! -f /opt/solr/solr.tgz ]; then
sudo -u solr /bin/bash - <<"EOF"
curl https://archive.apache.org/dist/lucene/solr/4.4.0/solr-4.4.0.tgz > /opt/solr/solr.tgz
tar xvfz /opt/solr/solr.tgz -C /opt/solr
chmod g+w /opt/solr/ -R
# TODO: see https://bitbucket.org/siovene/astrobin/issue/257/migrate-to-haystack-2x
sed -i '/EnglishPorterFilterFactory/d' /opt/solr/solr-4.4.0/example/solr/collection1/conf/schema.xml
sed -i '/<\/fields>/i<field name="_version_" type="slong" indexed="true" stored="true" multiValued="false"\/>' /opt/solr/solr-4.4.0/example/solr/collection1/conf/schema.xml
EOF
fi

sudo -u astrobin /bin/bash - <<"EOF"
. /venv/astrobin/dev/bin/activate
. /var/www/astrobin/env/dev

/var/www/astrobin/manage.py build_solr_schema > /opt/solr/solr-4.4.0/example/solr/collection1/conf/schema.xml
EOF
