#!/bin/sh
./manage.py build_solr_schema > schema.xml
sudo mv schema.xml /opt/solr/apache-solr-4.0.0-BETA/example/solr/collection1/conf/schema.xml 
