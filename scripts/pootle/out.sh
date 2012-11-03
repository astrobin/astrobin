#!/bin/bash
LANGS="ca de el es fi fr it nl pl pt pt-BR ro ru sk sq tr zh-CN"
FROM='po/astrobin/'
TO='../astrobin/astrobin/locale/'

echo "Syncing Pootle files to disk..."
../astrobin/venv/bin/python ./manage.py sync_stores

for lang in $LANGS
do
  echo "Copying $lang..."
  cp $FROM/$lang/django.po $TO/$lang/LC_MESSAGES/
done

echo "Done."
