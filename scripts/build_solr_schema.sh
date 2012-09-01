#!/bin/sh
./manage.py build_solr_schema > schema.xml
sudo mv schema.xml /opt/solr/apache-solr-3.6.1/example/solr/conf/schema.xml
