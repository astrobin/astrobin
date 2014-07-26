#!/bin/sh


# Setup postgresql
cp /var/www/astrobin/conf/pg_hba.conf /etc/postgresql/9.3/main/

sudo -u postgres /bin/sh <<"EOF"
psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='astrobin'" | grep -q 1 || createuser astrobin
psql -lqt | cut -d \| -f 1 | grep -w astrobin || createdb astrobin
EOF

sudo -u postgres psql <<"EOF"
alter user astrobin with encrypted password 's3cr3t';
grant all privileges on database astrobin to astrobin;
EOF
