#!/bin/bash

# Usage:
#
#    ./download.sh $ssh_cmd $pootle_host $remote_pootle_root
#
# e.g.:
#    ./download.sh "ssh -i auth.pem" user@host.com /opt/pootle

SSH=$1
HOST=$2
POOTLE_ROOT=$3

ARCHIVE=/tmp/astrobin_i18n_files

${SSH} ${HOST} /bin/bash <<-EOT
    sudo python ${POOTLE_ROOT}/bin/pootle sync_stores

    rm -rf ${ARCHIVE}
    mkdir -p ${ARCHIVE}

    for project in ${POOTLE_ROOT}/lib/pootle/translations/*; do
      for language in \$project/*; do

        project_name=\$(basename \$project)
        language_code=\$(basename \$language)

        src=\$language/\$project_name.po
        dest=${ARCHIVE}/\$project_name/locale/\$language_code/LC_MESSAGES

        if [[ "\${language_code}" == "templates" ]]; then
          src=\$language/\$project_name.pot
          dest=${ARCHIVE}/\$project_name/locale/en/LC_MESSAGES
        fi

        mkdir -p \$dest
        cp \$src \$dest/django.po
      done
    done
EOT

rsync -avz -e "${SSH}" ${HOST}:${ARCHIVE}/* .
