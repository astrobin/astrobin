#!/bin/bash
LANGS="ca de el es fi fr it nl pt pl pt-BR ro ru sk sq tr zh-CN"
FROM='../astrobin/astrobin/locale/'
TO='po/astrobin/'

for lang in $LANGS
do
  echo "Copying $lang..."
  cp $FROM/$lang/LC_MESSAGES/django.po $TO/$lang/
done

echo "Updating Pootle..."
../astrobin/venv/bin/python ./manage.py update_stores

echo "Done."
