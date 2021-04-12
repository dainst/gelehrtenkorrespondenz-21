#!/bin/bash

# This script is meant as documentation on how:
# - Annotations from the 2018 webanno project were matched to the new ocr
# It assumes that the docker image container from `make build` is available

mkdir -p /tmp/webanno-match/output

# Download exports file "webanno-exports-original-annotations.zip"
curl https://cumulus.dainst.org/index.php/s/pakSCJzAdSZTai9/download -C - -o /tmp/webanno-match/exports.zip
unzip -o -d /tmp/webanno-match /tmp/webanno-match/exports.zip

# Use the Exports together with the new ocr and the match script
# This prints a list of unmatched annotations and writes the new
# tsv files to the outputs dir.
docker run -it --rm \
  --volume /tmp/webanno-match:/tmp/workdir \
  dainst/glk21:dev \
  src/match_webanno_ocr.py /app/data/texts /tmp/workdir/webanno-exports -o /tmp/workdir/output -p
