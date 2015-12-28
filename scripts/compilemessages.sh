#!/bin/bash
apps="astrobin rawdata nested_comments astrobin_apps_users astrobin_apps_images astrobin_apps_platesolving astrobin_apps_donations astrobin_apps_premium"

for app in $apps; do
    echo "Processing app: $app"
    (cd $app; ../manage.py compilemessages)
done

