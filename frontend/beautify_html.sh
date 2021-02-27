#!/bin/sh

for f in `find src -name '*.html'`; do
  ./node_modules/.bin/js-beautify -f $f -r -w 120 -s 2
done
