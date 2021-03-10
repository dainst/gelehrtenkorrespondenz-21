#!/bin/bash

set -e

ZENON_ID_FILE="$1"
IMAGES_DIR="$2"
OUTPUT_DIR="$3"

mkdir -p "${OUTPUT_DIR}/pdf" \
         "${OUTPUT_DIR}/txt"

cat "$ZENON_ID_FILE" | while read ZENON_ID
do
    OUT_PDF="${OUTPUT_DIR}/pdf/${ZENON_ID}.pdf"
    OUT_TXT="${OUTPUT_DIR}/txt/${ZENON_ID}.txt"

    # Do not convert if both output files exist
    if [ -s "$OUT_PDF" -a -s "$OUT_TXT" ]
    then
        echo "Already converted: ${ZENON_ID}"
        continue
    fi

    # Image filenames contain the Zenon id with leading 0s truncated
    SHORT_ID=$(echo $ZENON_ID | sed 's/^0\+//g')
    BOOK_PREFIX="BOOK-${SHORT_ID}"

    # create a pdf compressing those image files starting with the prefix
    # NOTE: Somehow jbig2 and pdf.py do not like /tmp or temporary
    #       directories, so we create a dir in the output dir.
    JBIG_DIR="${OUTPUT_DIR}/jbig2/${BOOK_PREFIX}"
    mkdir -p "$JBIG_DIR"
    jbig2 --symbol-mode --pdf \
        -b "${JBIG_DIR}/output" \
        "${IMAGES_DIR}/${BOOK_PREFIX}"*.jpg
    pdf.py "${JBIG_DIR}/output" > "${JBIG_DIR}/${BOOK_PREFIX}.pdf"

    # use the newly created pdf as input for ocrmypdf
    ocrmypdf \
        --quiet \
        --language deu \
        --fast-web-view 0 \
        --clean \
        --deskew \
        --optimize 2 \
        --jbig2-lossy \
        --title "$BOOK_PREFIX" \
        --sidecar "$OUT_TXT" \
        "${JBIG_DIR}/${BOOK_PREFIX}.pdf" \
        "$OUT_PDF"

    # cleanup the directory with the jbig2 files and input pdf
    rm -r "$JBIG_DIR"

    echo "OK: ${ZENON_ID}"
done
