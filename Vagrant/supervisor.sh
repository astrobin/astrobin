#!/bin/bash

cp /var/www/astrobin/conf/supervisord/* /etc/supervisor/conf.d/
mkdir -p /var/log/{celery,gunicorn,nginx,solr}
