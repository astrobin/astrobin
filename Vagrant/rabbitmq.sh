#!/bin/bash

rabbitmqctl add_user astrobin s3cr3t
rabbitmqctl add_vhost astrobin
rabbitmqctl set_permissions -p astrobin astrobin ".*" ".*" ".*"
