#!/bin/sh
echo "Remember to run this from astrobin's top source dir."
echo "Use mysql root password below."
mysql -u root -p < sql/reset_db.sql
./scripts/syncdb.sh
./scripts/create_objects_db.sh
