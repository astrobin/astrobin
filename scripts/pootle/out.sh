#!/bin/bash
LANGS="ca cs de el es fa fi fr it hu nl pl pt pt-BR ro ru sk sq sr tr zh-CN"
PROJECTS="astrobin nested_comments rawdata astrobin_apps_users astrobin_apps_images astrobin_apps_platesolving"
TO='/home/astrobin/code/astrobin'
FROM='/home/astrobin/venv/translate.astrobin.com/lib/python2.7/site-packages/pootle/po'



echo "Syncing Pootle files to disk..."
pootle sync_stores

for proj in $PROJECTS
do
    echo "* $proj"
    for lang in $LANGS
    do
        echo "  Copying $lang..."
        cp $FROM/$proj/$lang/django.po $TO/$proj/locale/$lang/LC_MESSAGES/
    done
done

echo "Done."

