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

ARCHIVE=/tmp/astrobin_ng_i18n_files

${SSH} ${HOST} /bin/bash <<-EOT
    sudo python ${POOTLE_ROOT}/bin/pootle sync_stores

    rm -rf ${ARCHIVE}
    mkdir -p ${ARCHIVE}

    for language in ${POOTLE_ROOT}/lib/pootle/translations/astrobin_angular_app/*; do
      language_code=\$(basename -- \$language)
      project_name="astrobin_angular_app"
      src=\$language/\$project_name.po
      dest=${ARCHIVE}/\$language_code.po

      if [[ "\${language_code}" == "templates" ]]; then
        src=\$language/\$project_name.pot
        dest=${ARCHIVE}/en.po
      fi

      cp \$src \$dest
    done
EOT

rsync -avz -e "${SSH}" ${HOST}:${ARCHIVE}/* ../astrobin-ng/src/assets/i18n/
