#!/usr/bin/env bash

if [ "$#" -ne 2 ]
then
    echo "Usage: $0 <directory> <days>"
    echo " - Deletes files older than <days> days from <directory>."
    exit 1
fi

find $1 -type f -name '*' -mtime +$2 -exec rm {} \;
