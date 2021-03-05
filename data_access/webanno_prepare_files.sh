#!/bin/bash

# Two arguments: The directories to extract from and to
ZIPS_DIR=$1
OUT_DIR=$2

# Extract files
ls "${ZIPS_DIR}/"*.zip | while read archive
do
  EXT_DIR="${OUT_DIR}/$(basename -s.zip "$archive")"
  mkdir -p $EXT_DIR
  unzip -o -d "$EXT_DIR" "$archive"
done

# Fix unicode escapes in the annotation files
find "${OUT_DIR}" -type f -path '*annotation/*.tsv' | while read file
do
  sed -i 's|\\u00A3|£|g' "$file"
  sed -i 's|\\u00A5|¥|g' "$file"
  sed -i 's|\\u00A7|§|g' "$file"
  sed -i 's|\\u00A9|©|g' "$file"
  sed -i 's|\\u00AB|«|g' "$file"
  sed -i 's|\\u00AE|®|g' "$file"
  sed -i 's|\\u00B0|°|g' "$file"
  sed -i 's|\\u00B1|±|g' "$file"
  sed -i 's|\\u00B7|·|g' "$file"
  sed -i 's|\\u00BB|»|g' "$file"
  sed -i 's|\\u00C4|Ä|g' "$file"
  sed -i 's|\\u00C9|É|g' "$file"
  sed -i 's|\\u00CC|Ì|g' "$file"
  sed -i 's|\\u00D6|Ö|g' "$file"
  sed -i 's|\\u00DC|Ü|g' "$file"
  sed -i 's|\\u00DF|ß|g' "$file"
  sed -i 's|\\u00E0|à|g' "$file"
  sed -i 's|\\u00E4|ä|g' "$file"
  sed -i 's|\\u00E8|è|g' "$file"
  sed -i 's|\\u00E9|é|g' "$file"
  sed -i 's|\\u00EC|ì|g' "$file"
  sed -i 's|\\u00F2|ò|g' "$file"
  sed -i 's|\\u00F3|ó|g' "$file"
  sed -i 's|\\u00F6|ö|g' "$file"
  sed -i 's|\\u00FC|ü|g' "$file"
  sed -i 's|\\u2014|—|g' "$file"
  sed -i 's|\\u2018|‘|g' "$file"
  sed -i 's|\\u2019|’|g' "$file"
  sed -i 's|\\u201D|”|g' "$file"
  sed -i 's|\\u201E|„|g' "$file"
  sed -i 's|\\u2022|•|g' "$file"
  sed -i 's|\\u20AC|€|g' "$file"
  sed -i 's|\\u25A0|■|g' "$file"
  sed -i 's|\\u2666|♦|g' "$file"
done
