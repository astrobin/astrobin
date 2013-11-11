#!/bin/bash
LANGS="ca cs de el es fa fi fr it hu nl pt pl pt-BR ro ru sk sq sr tr zh-CN"
PROJECTS="astrobin nested_comments rawdata astrobin_apps_users astrobin_apps_images astrobin_apps_platesolving"
FROM='../astrobin-1.10'
TO='po'

for proj in $PROJECTS
do
    echo "* $proj"
    for lang in $LANGS
    do
        echo "   Copying $lang..."
        cp $FROM/$proj/locale/$lang/LC_MESSAGES/django.po $TO/$proj/$lang/
    done
done

echo "Updating Pootle..."
./manage.py update_stores

echo "Done."

