#!/usr/bin/env bash

if [ "$#" -ne 2 ]
then
    echo "Usage: $0 <directory> <minutes>"
    echo " - Deletes files older than <minutes> minutes from <directory>."
    exit 1
fi

find $1 -type f -name '*' -mmin +$2 -exec rm {} \;
