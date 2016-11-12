#!/bin/bash
LANGS="ar be ca cs de el es fa fi fr it hu ja nl pl pt pt-BR ro ru sk sq sr tr zh-CN zh-TW"
PROJECTS="astrobin nested_comments rawdata astrobin_apps_users astrobin_apps_images astrobin_apps_platesolving astrobin_apps_donations astrobin_apps_premium astrobin_apps_groups change_email"
TO='/var/www/astrobin'
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

