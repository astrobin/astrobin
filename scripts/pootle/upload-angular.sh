#!/bin/bash

# Usage:
#
#    ./upload.sh $ssh_cmd $pootle_host $remote_pootle_root
#
# e.g.:
#    ./upload.sh "ssh -i auth.pem" user@host.com /opt/pootle

FILES=$(find ../astrobin-ng/src/assets/i18n -name *.po)

SSH=$1
HOST=$2
POOTLE_ROOT=$3

TMPDIR=$(mktemp -d -t astrobin-ng)

for FILE in ${FILES}; do
    echo "Processing ${FILE}..."
    APP="astrobin_angular_app"
    FILENAME=$(basename -- "${FILE}")
    LANG=${FILENAME%.*}
    EXT="po"

    if [[ "${LANG}" == "en" ]]; then
        LANG="templates"
        EXT="pot"
    fi

    mkdir -p ${TMPDIR}/${APP}/${LANG}
    cp ${FILE} ${TMPDIR}/${APP}/${LANG}/${APP}.${EXT}
done

rsync -avz -e "${SSH}" ${TMPDIR}/* ${HOST}:${POOTLE_ROOT}/lib/pootle/translations
${SSH} ${HOST} -t sudo python ${POOTLE_ROOT}/bin/pootle update_stores
