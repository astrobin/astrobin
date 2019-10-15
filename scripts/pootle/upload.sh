#!/bin/bash

# Usage:
#
#    ./upload.sh $ssh_cmd $pootle_host $remote_pootle_root
#
# e.g.:
#    ./upload.sh "ssh -i auth.pem" user@host.com /opt/pootle

FILES=$(find . -name *.po | grep -v "^./src")

SSH=$1
HOST=$2
POOTLE_ROOT=$3

TMPDIR=$(mktemp -d -t astrobin)

for FILE in ${FILES}; do
    echo "Processing ${FILE}..."
    APP=$(echo ${FILE} | awk -F "/" '{print $2}')
    LANG=$(echo ${FILE} | awk -F "/" '{print $4}')
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
