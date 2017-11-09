#!/bin/bash

# Please run this script as the user vagrant if installing in Vagrant, or as
# root if running directly to install on a real server.

SUDO='sudo -E'

ROOT="/var/www/astrobin"
DEV="${ROOT}/env/dev"

function astrobin_log {
    echo -e " - $1" >&3
}

function astrobin_err {
    local COLOR="tput setaf 1; tput setab 3; tput bold"
    local COLOR_RST="tput sgr 0"

    astrobin_log "ERROR: $1"
    exit 1
}


function abort {
    astrobin_err "SOMETHING WENT WRONG! Please check vagrant.log for more details."
}

function begin {
    astrobin_log "#################################################################"
    astrobin_log "### Initializing AstroBin Vagrant environment"
    astrobin_log "#################################################################"
}

function check {
    local EXAMPLE="${ROOT}/env/example"

    # Check env/dev
    if [ ! -f $DEV ]; then
        astrobin_err "You need to copy env/example to env/dev and configure the needed variables."
    fi

    local VARS=(
        ASTROBIN_DEBUG
        ASTROBIN_BASE_URL
        ASTROBIN_SHORT_BASE_URL
        ASTROBIN_HOST
        ASTROBIN_SERVER_EMAIL
        ASTROBIN_DEFAULT_FROM_EMAIL
        ASTROBIN_EMAIL_SUBJECT_PREFIX
        ASTROBIN_EMAIL_HOST_USER
        ASTROBIN_EMAIL_HOST_PASSWORD
        ASTROBIN_EMAIL_HOST
        ASTROBIN_EMAIL_PORT
        ASTROBIN_EMAIL_USE_TLS
        ASTROBIN_DATABASE_HOST
        ASTROBIN_DATABASE_NAME
        ASTROBIN_DATABASE_USER
        ASTROBIN_DATABASE_PASSWORD
        ASTROBIN_DJANGO_SECRET_KEY
        ASTROBIN_AWS_S3_ENABLED
        ASTROBIN_LOCAL_STATIC_STORAGE
        ASTROBIN_AWS_ACCESS_KEY_ID
        ASTROBIN_AWS_SECRET_ACCESS_KEY
        ASTROBIN_AWS_STORAGE_BUCKET_NAME
        ASTROBIN_IMAGES_URL
        ASTROBIN_CDN_URL
        ASTROBIN_FLICKR_API_KEY
        ASTROBIN_FLICKR_SECRET
        ASTROBIN_HAYSTACK_BACKEND_URL
        ASTROBIN_BROKER_URL
        ASTROMETRY_NET_API_KEY
        ASTROBIN_RAWDATA_ROOT
        ASTROBIN_PAYPAL_MERCHANT_ID
        ASTROBIN_MIN_INDEX_TO_LIKE
        ASTROBIN_GOOGLE_ANALYTICS_ID
        ASTROBIN_ADS_ENABLED
        ASTROBIN_DONATIONS_ENABLED
        ASTROBIN_PREMIUM_ENABLED
    )

    local FILES=(
        ${DEV}
    )

    for FILE in ${FILES[@]}; do
        for VAR in ${VARS[@]}; do
            astrobin_log "Checking ${FILE} for ${VAR}..."
            if ! grep -q "${VAR}" ${FILE}; then
                astrobin_err "The environment variable ${VAR} is not defined in ${FILE}"
            fi
        done
    done
}

function init_system {
    # Create directories
    astrobin_log "Creating directories..."
    mkdir -p /var/www/media
    mkdir -p /var/www/tmpzips
    mkdir -p /rawdata/files
    mkdir -p /venv
    mkdir -p /var/log/astrobin

    astrobin_log "Creating groups..."
    groupadd -g 2000 astrobin

    astrobin_log "Adding users..."
    if ! id -u astrobin >/dev/null 2>&1; then
        useradd -m -s /bin/bash -g astrobin -u 2000 astrobin
        usermod -a -G sudo astrobin
    fi

    if id -u vagrant >/dev/null 2>&1; then
        usermod -G astrobin vagrant
    fi

    astrobin_log "Setting ownerships..."
    chown -R astrobin:astrobin /venv
    chown -R astrobin:astrobin /var/www/media
    chown -R astrobin:astrobin /var/www/tmpzips
    chown -R astrobin:astrobin /rawdata
    chown -R astrobin:astrobin /var/log/astrobin

    chmod g+w /venv
    chmod g+w /var/www/media
    chmod g+w /rawdata
    chmod g+w /var/log/astrobin

    astrobin_log "Customizing astrobin's home directory..."
    if grep -q DebuggingServer /home/astrobin/.bashrc; then
        astrobin_log "Debug smpt server already setup"
    else
        echo "nc -z 127.0.0.1 1025 || python -m smtpd -n -c DebuggingServer localhost:1025 &" >> /home/astrobin/.bashrc
    fi

    astrobin_log "Setting locale..."
    $SUDO locale-gen "en_US.UTF-8"
    $SUDO dpkg-reconfigure -f noninteractive locales
}

function apt {
    # Init
    astrobin_log "Updating package manager..."
    $SUDO apt-get update && \

    astrobin_log "Upgrading packags..." && \
    $SUDO apt-get -y --force-yes upgrade && \


    # Install packages
    astrobin_log "Installing new packages..." && \
    $SUDO apt-get -y install \
        figlet cowsay \
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
        python-virtualenv \
        elasticsearch \
        redis-server \
        gettext \
        python-pyside libpyside-dev \
        libqjson-dev libraw-dev \
        shiboken libshiboken-dev \
        libjpeg62 libjpeg62-dev \
        libfreetype6 libfreetype6-dev \
        zlib1g-dev \
        default-jre \
        node-less && \

    astrobin_log "Setting up symboling links..." && \
    $SUDO rm -rf /usr/lib/libjpeg.so && \
    $SUDO rm -rf /usr/lib/libfreetype.so && \
    $SUDO rm -rf /usr/lib/libz.so && \

    $SUDO ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/ && \
    $SUDO ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/ && \
    $SUDO ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
}

function pip {
    astrobin_log "Installing dependencies..."

    $SUDO -H -u astrobin /bin/bash - <<"EOF"
    virtualenv --no-site-packages /venv/astrobin/dev
    . /venv/astrobin/dev/bin/activate

    # Install python requirements
    LCALL=C pip install -U pip setuptools
    LCALL=C pip install --no-deps -r /var/www/astrobin/requirements.txt

    # Install submodules
    (cd /var/www/astrobin/ && git submodule init && git submodule update)
    for d in /var/www/astrobin/submodules/*; do
        (
            cd $d;
            if [ -f setup.py ];
            then
                python setup.py install
            fi
        );
    done
EOF
}

function postgres {
    local PSQL_V="`psql -V | egrep -o '[0-9]{1,}\.[0-9]{1,}'`"
    # Setup postgresql
    astrobin_log "Creating postgres cluster..."
    $SUDO pg_createcluster $PSQL_V main --start

    function postgres_db {
        astrobin_log "Setting up database..."
        $SUDO -u postgres /bin/sh <<"EOF"
        psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='astrobin'" | grep -q 1 || createuser astrobin
        psql -lqt | cut -d \| -f 1 | grep -w astrobin || createdb astrobin
EOF
    }

    function postgres_priv {
        local PASSWORD=`grep "export *ASTROBIN_DATABASE_PASSWORD" $DEV | tr "'" '"' | awk -F\" '{print $2}'`
        $SUDO -u postgres psql <<EOF
        alter user astrobin with encrypted password '$PASSWORD';
        alter user astrobin createdb;
        grant all privileges on database astrobin to astrobin;
EOF
    }

    postgres_db && postgres_priv
}

function abc {
    astrobin_log "Setting up 'abc'..."
    . /venv/astrobin/dev/bin/activate

    (
        cd /var/www/astrobin/submodules/abc/cfitsio; \
        ./configure && make -j4
    ) && \

    # Force out of source build because symbolic links would cause trouble
    # in case of Windows hosts.
    (
        mkdir -p /tmp/libabc_build; \
        cd /tmp/libabc_build; \
        qmake /var/www/astrobin/submodules/abc && make -j 4 && $SUDO make install
    )
}

function elasticsearch {
    astrobin_log "Setting up ElasticSearch..."
    $SUDO sed -i 's/#START_DAEMON/START_DAEMON/' /etc/default/elasticsearch
    $SUDO systemctl enable elasticsearch
    $SUDO systemctl restart elasticsearch
}

function astrobin {
    echo "Preparing AstroBin..."

    $SUDO -u astrobin /bin/bash - <<EOF
    # Initialize the environment
    . /venv/astrobin/dev/bin/activate
    . $DEV

    # Automatically activating the environment upon login
    if [ ! -f /home/astrobin/.profile.customized ]; then
        touch /home/astrobin/.profile.customized &&
        echo "source /venv/astrobin/dev/bin/activate" >> /home/astrobin/.profile &&
        echo "source $DEV" >> /home/astrobin/.profile &&
        echo "cd /var/www/astrobin" >> /home/astrobin/.profile
    fi

    if [ ! -f /home/astrobin/.bashrc.customized ]; then
        touch /home/astrobin/.bashrc.customized
        echo "figlet WELCOME TO ASTROBIN" >> /home/astrobin/.bashrc
        echo "cowsay You can run a development server with: ./manage.py runserver 0.0.0.0:8083, and remember to read ./INSTALL.md\!" >> /home/astrobin/.bashrc
    fi

    # Initialize db
    /var/www/astrobin/manage.py migrate
    /var/www/astrobin/manage.py migrate --run-syncdb
    /var/www/astrobin/manage.py sync_translation_fields --noinput

    # Create Premium groups
    echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='astrobin_lite')" | /var/www/astrobin/manage.py shell
    echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='astrobin_premium')" | /var/www/astrobin/manage.py shell

    # Create moderation groups
    echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='content_moderators')" | /var/www/astrobin/manage.py shell
    echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='image_moderators')" | /var/www/astrobin/manage.py shell

    # Create Raw Data groups
    echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='rawdata_atom')" | /var/www/astrobin/manage.py shell

    # Create IOTD board groups
    echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='iotd_staff')" | /var/www/astrobin/manage.py shell
    echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='iotd_submitters')" | /var/www/astrobin/manage.py shell
    echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='iotd_reviewers')" | /var/www/astrobin/manage.py shell
    echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='iotd_judges')" | /var/www/astrobin/manage.py shell

    # Create superuser
    echo "from django.contrib.auth.models import User; User.objects.filter(email='dev@astrobin.com').delete(); User.objects.create_superuser('astrobin_dev', 'dev@eastrobin.com', 'astrobin_dev')" | python manage.py shell

    # Assign superuser to some groups
    echo "from django.contrib.auth.models import User, Group; u = User.objects.get(username='astrobin_dev'); g = Group.objects.get(name='content_moderators'); g.user_set.add(u)" | /var/www/astrobin/manage.py shell
    echo "from django.contrib.auth.models import User, Group; u = User.objects.get(username='astrobin_dev'); g = Group.objects.get(name='image_moderators'); g.user_set.add(u)" | /var/www/astrobin/manage.py shell

    # Collect static files
    /var/www/astrobin/manage.py collectstatic --noinput

    # Create Site
    echo "from django.contrib.sites.models import Site; Site.objects.get_or_create(name='AstroBin', domain='localhost')" | /var/www/astrobin/manage.py shell

    # Compile messages
    (cd /var/www/astrobin/; ./scripts/compilemessages.sh)

    # Run tests
    (cd /var/www/astrobin/; ./scripts/test.sh)
EOF
}

function end {
    astrobin_log "#################################################################"
    astrobin_log "### All done!"
    astrobin_log "#################################################################"
}

if [ "$1" != "1" ]; then
    exec 3>&1 &>/var/www/astrobin/vagrant.log
else
    exec 3>&1
fi

check

(
    begin && \
    init_system && \
    apt && \
    pip && \
    postgres && \
    abc && \
    elasticsearch && \
    astrobin && \
    end
) || abort
