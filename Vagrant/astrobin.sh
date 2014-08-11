#!/bin/bash

function astrobin_log {
    echo $1 >&3
}

function abort {
    astrobin_log "SOMETHING WENT WRONG!"
    astrobin_log "Please check vagrant.log for more details."
    exit 1
}

function begin {
    astrobin_log "#################################################################"
    astrobin_log "### Initializing AstroBin Vagrant environment"
    astrobin_log "#################################################################"
}

function init_system {
    # Create directories
    astrobin_log " - Creating directories..."
    mkdir -p /var/www/media
    mkdir -p /rawdata/files
    mkdir -p /opt/solr
    mkdir -p /venv
    mkdir -p /var/log/astrobin

    astrobin_log " - Creating groups..."
    groupadd -g 2000 astrobin

    astrobin_log " - Adding users..."
    if ! id -u astrobin >/dev/null 2>&1; then
        useradd -MN -s /dev/null -g astrobin -u 2000 astrobin
    fi

    if ! id -u solr >/dev/null 2>&1; then
        useradd -MN -s /dev/null -g astrobin -u 2001 solr
    fi

    if id -u vagrant >/dev/null 2>&1; then
        usermod -G astrobin vagrant
    fi

    astrobin_log " - Setting ownerships..."
    chown -R astrobin:astrobin /venv
    chown -R astrobin:astrobin /var/www/media
    chown -R astrobin:astrobin /rawdata
    chown -R solr:astrobin /opt/solr
    chown -R astrobin:astrobin /var/log/astrobin

    chmod g+w /venv
    chmod g+w /var/www/media
    chmod g+w /rawdata
    chmod g+w /opt/solr
    chmod g+w /var/log/astrobin
}

function apt {
    # Init
    astrobin_log " - Upgrading packages..."
    apt-get update && apt-get -y upgrade && \


    # Install packages
    astrobin_log " - Installing new packages..." && \
    apt-get -y install \
        pkg-config \
        nginx \
        memcached \
        postgresql \
        libpq-dev \
        python-pip \
        python-dev \
        git \
        libxslt1-dev \
        libxml2-dev \
        cmake \
        qt4-qmake \
        libqt4-dev \
        sudo \
        python-virtualenv \
        supervisor \
        rabbitmq-server \
        python-pyside libpyside-dev \
        libqjson-dev libraw-dev \
        shiboken libshiboken-dev \
        libjpeg62 libjpeg62-dev \
        libfreetype6 libfreetype6-dev \
        zlib1g-dev \
        default-jre && \

    astrobin_log " - Setting up symboling links..." && \
    rm -rf /usr/lib/libjpeg.so && \
    rm -rf /usr/lib/libfreetype.so && \
    rm -rf /usr/lib/libz.so && \

    ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/ && \
    ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/ && \
    ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
}

function pip {
    venv_log=$(astrobin_log " - Setting up virtualenv...")
    req_log=$(astrobin_log " - Installing python requirements...")
    sub_log=$(astrobin_log " - Installing submodules...")

    sudo -u astrobin /bin/bash - <<"EOF"
    $venv_log
    virtualenv --no-site-packages /venv/astrobin/dev
    . /venv/astrobin/dev/bin/activate

    # Install python requirements
    $req_log
    pip install -r /var/www/astrobin/requirements.txt

    # Install submodules
    $sub_log
    for d in /var/www/astrobin/submodules/*; do
        (
            cd $d;
            if [ -f setup.py ];
            then
                python setup.py install
            fi
        );
    done

    # TODO: No idea why...
    (cd /venv/astrobin/dev/src/django-contrib-requestprovider/gadjolib/; python setup.py install)
EOF
}

function postgres {
    # Setup postgresql
    astrobin_log " - Copying postgres conf file..."
    cp /var/www/astrobin/conf/pg_hba.conf /etc/postgresql/9.3/main/

    function postgres_db {
        astrobin_log " - Setting up database..."
        sudo -u postgres /bin/sh <<"EOF"
        psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='astrobin'" | grep -q 1 || createuser astrobin
        psql -lqt | cut -d \| -f 1 | grep -w astrobin || createdb astrobin
EOF
    }

    function postgres_priv {
        sudo -u postgres psql <<"EOF"
        alter user astrobin with encrypted password 's3cr3t';
        alter user astrobin createdb;
        grant all privileges on database astrobin to astrobin;
EOF
    }

    postgres_db && postgres_priv
}

function rabbitmq {
    astrobin_log " - Setting up rabbitmq..."
    rabbitmqctl add_user astrobin s3cr3t
    rabbitmqctl add_vhost astrobin
    rabbitmqctl set_permissions -p astrobin astrobin ".*" ".*" ".*"
}

function supervisor {
    astrobin_log " - Setting up supervisor..."
    cp /var/www/astrobin/conf/supervisord/* /etc/supervisor/conf.d/
    mkdir -p /var/log/{celery,gunicorn,nginx,solr}
}

function abc {
    astrobin_log " - Setting up 'abc'..."
    . /venv/astrobin/dev/bin/activate

    (
        cd /var/www/astrobin/submodules/abc/cfitsio; \
        ./configure && make -j4
    ) && \

    (
        cd /var/www/astrobin/submodules/abc; \
        qmake && make -j4 && make install
    )
}

function astrobin {
    syndb_log=$(astrobin_log " - Syncing database...")
    migrate_log=$(astrobin_log " - Migrating database...")
    trans_log=$(astrobin_log " - Syncing translation fields...")
    static_log=$(astrobin_log " - Collecting static files...")

    sudo -u astrobin /bin/bash - <<"EOF"
    # Initialize the environment
    . /venv/astrobin/dev/bin/activate
    . /var/www/astrobin/env/dev

    # Initialize db
    $sync_db_log && \
    /var/www/astrobin/manage.py syncdb --noinput && \

    $migrate_log && \
    /var/www/astrobin/manage.py migrate && \

    $trans_log && \
    /var/www/astrobin/manage.py sync_translation_fields --noinput && \

    $static_log && \
    /var/www/astrobin/manage.py collectstatic --noinput
EOF
}

function db {
    astrobin_log " - Initializing database data..."
    sudo -u postgres psql -d astrobin <<"EOF"
COPY auth_group (id, name) FROM stdin;
1	Producers
2	Retailers
3	Paying
4	affiliate-1
5	affiliate-10
6	affiliate-50
7	affiliate-100
8	affiliate-inf
9	retailer-affiliate-1
11	retailer-affiliate-10
12	retailer-affiliate-50
13	retailer-affiliate-100
14	retailer-affiliate-inf
100	everyone
1000	rawdata-meteor
1001	rawdata-luna
1002	rawdata-sol
1003	rawdata-galaxia
2000	astrobin-donor-coffee-monthly
2001	astrobin-donor-snack-monthly
2002	astrobin-donor-pizza-monthly
2003	astrobin-donor-movie-monthly
2004	astrobin-donor-dinner-monthly
2005	astrobin-donor-coffee-yearly
2006	astrobin-donor-snack-yearly
2007	astrobin-donor-pizza-yearly
2008	astrobin-donor-movie-yearly
2009	astrobin-donor-dinner-yearly
3000	IOTD_Staff
\.

COPY subscription_subscription (id, name, description, price, recurrence_period, recurrence_unit, group_id, trial_period, trial_unit) FROM stdin;
1	Meteor	5 GB	2.95	1	M	1000	7	D
2	Luna	100 GB	9.95	1	M	1001	7	D
3	Sol	250 GB	19.95	1	M	1002	7	D
4	Galaxia	500 GB	49.95	1	M	1003	7	D
5	AstroBin Donor Coffee Monthly		2.50	1	M	2000	0	D
6	AstroBin Donor Snack Monthly		3.50	1	M	2001	0	D
7	AstroBin Donor Movie Monthly		10.00	1	M	2002	0	D
8	AstroBin Donor Dinner Monthly		25.00	1	M	2003	0	D
9	AstroBin Donor Coffee Yearly		24.00	1	Y	2004	0	D
10	AstroBin Donor Snack Yearly		34.00	1	Y	2005	0	D
11	AstroBin Donor Pizza Yearly		60.00	1	Y	2006	0	D
12	AstroBin Donor Movie Yearly		100.00	1	Y	2007	0	D
13	AstroBin Donor Dinner Yearly		250.00	1	Y	2008	0	D
14	AstroBin Donor Pizza Monthly		6.00	1	M	2009	0	D
\.
EOF
}

function solr {
    astrobin_log " - Setting up solr..."

    local return_value=0

    dl_log=$(astrobin_log " - Downloading solr...")
    tar_log=$(astrobin_log " - Extracting solr...")
    schema_log=$(astrobin_log " - Building solr schema...")
    cust_log=$(astrobin_log " - Customizing solr schema...")

    if [ ! -f /opt/solr/solr.tgz ]; then
        sudo -u solr /bin/bash - <<"EOF"
        $dl_log
        curl https://archive.apache.org/dist/lucene/solr/4.4.0/solr-4.4.0.tgz > /opt/solr/solr.tgz && \

        $tar_log && \
        tar xvfz /opt/solr/solr.tgz -C /opt/solr && \
        chmod g+w /opt/solr/ -R

        [ $? -eq 0 ] && return_value=0
EOF
    fi

    sudo -u astrobin /bin/bash - <<"EOF"
    . /venv/astrobin/dev/bin/activate
    . /var/www/astrobin/env/dev

    $schema_log
    /var/www/astrobin/manage.py build_solr_schema > /opt/solr/solr-4.4.0/example/solr/collection1/conf/schema.xml

    $cust_log
    # TODO: see https://bitbucket.org/siovene/astrobin/issue/257/migrate-to-haystack-2x
    sed -i '/EnglishPorterFilterFactory/d' /opt/solr/solr-4.4.0/example/solr/collection1/conf/schema.xml
    sed -i '/<\/fields>/i<field name="_version_" type="slong" indexed="true" stored="true" multiValued="false"\/>' /opt/solr/solr-4.4.0/example/solr/collection1/conf/schema.xml
EOF

    if [ $return_value -eq 0 ]; then
        true
    else
        false
    fi
}

function end {
    astrobin_log "#################################################################"
    astrobin_log "### All done!"
    astrobin_log "#################################################################"
}


if [ "$1" != "1" ]; then
    echo " - Running in quiet mode..."
    exec 3>&1 &>/vagrant/vagrant.log
else
    echo " - Running in verbose mode..."
    exec 3>&1
fi


(
    begin && \
    init_system && \
    apt && \
    pip && \
    postgres && \
    rabbitmq && \
    supervisor && \
    abc && \
    astrobin && \
    db && \
    solr && \
    end
) || abort
