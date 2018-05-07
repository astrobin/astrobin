#!/bin/bash
apps="astrobin rawdata nested_comments astrobin_apps_users astrobin_apps_images astrobin_apps_platesolving astrobin_apps_donations astrobin_apps_premium astrobin_apps_groups"
langs="ar be ca cs de el en es fa fi fr hu it ja nl pl pt-BR pt ro ru sk sq sr tr zh-CN zh-TW"
manage="../manage.py"

echo "Processing apps..."
for app in $apps; do
    echo " * $app"
    for lang in $langs; do
        echo -n " $lang: "
        (cd $app; python $manage compilemessages -l $lang)
    done
    echo
done

