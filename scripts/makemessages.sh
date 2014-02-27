#!/bin/bash
apps="astrobin rawdata nested_comments astrobin_apps_users astrobin_apps_images astrobin_apps_platesolving astrobin_apps_donations"
langs="ar ca cs de el en es fa fi fr hu it ja nl pl pt-BR pt ro ru sk sq sr tr zh-CN zh-TW"

for app in $apps; do
    echo "Processing app: $app"
    for lang in $langs; do
        (cd $app; django-admin.py makemessages -l $lang -e html,txt,py -i *zinnia*)
    done
done

