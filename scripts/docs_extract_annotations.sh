#!/bin/bash

# This script is meant as documentation on how:
# - Corrected annotations from the ocr-matches were imported into the git repo
# It assumes that the docker image container from `make build` is available

mkdir -p /tmp/workdir/exports \
         /tmp/workdir/annotations

# Download exports file "webanno-exports-new-ocr-matched-corrected.zip"
#curl https://cumulus.dainst.org/index.php/s/yWsL8Ms2DE37ycd/download -C - -o /tmp/workdir/exports.zip
#unzip -o -d /tmp/workdir/exports /tmp/workdir/exports.zip

# copy the source files with annotations into place
cp /tmp/workdir/exports/*/source/*.tsv /tmp/workdir/annotations

# If there are corrections made by marina, overwrite the annotations files
find /tmp/workdir/exports/ -name "marina.tsv" | while read f
do
  page_file_name=$(basename $(dirname "$f"))
  cp -v "$f" "/tmp/workdir/annotations/${page_file_name}"
done

# sort annotations into directories named by their zenon id
cd /tmp/workdir/annotations
ls | egrep -o '^[^\_]+' | sort | uniq | xargs mkdir
find . -type d | while read d; do mv -v "$(basename $d)_page"* "$d"; done
