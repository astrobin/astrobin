#!/usr/bin/env bash

if [ "$#" -ne 2 ]
then
	echo "Usage: $0 directory max_kb"
	exit 1
fi

DIR=$1
MAX_KB=$2
KB=`du -s $DIR | awk '{print $1}'`
KEEP_PERCENT=20

if [ "$KB" -gt "$MAX_KB" ]
then
	FILES_NO=`ls -l $DIR | wc -l`
	let "del_threshold = $FILES_NO / $KEEP_PERCENT"
	let "keep_threshold = $FILES_NO - $del_threshold"
	echo "Preparing to delete $del_threshold oldest files, keeping $keep_threshold..."
	(cd $DIR; ls -t | sed -e "1,${keep_threshold}d" | xargs -d '\n' rm)
	echo "Current disk usage: $(du -sh $DIR | awk '{print $1}')"
else
	echo "We're good."
	exit 0
fi
