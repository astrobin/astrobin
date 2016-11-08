#!/bin/sh
./manage.py build_solr_schema > schema.xml
sudo mv schema.xml /opt/solr/solr-4.9.1/example/solr/collection1/conf/schema.xml 
