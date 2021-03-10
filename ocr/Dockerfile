
# While there is an official docker image for ocrmypdf with jbgig2enc included
# (at https://hub.docker.com/r/jbarlow83/ocrmypdf ) we experienced hard-to-diagnose
# errors with that image and ocrmypdfs jbig2 decoding in the OCR step.
FROM ubuntu:20.10

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y \
        # dependencies to fetch and build jbig2
        curl ca-certificates \
        build-essential autoconf automake libtool \
        libleptonica-dev \
        zlib1g-dev \
        # dependencies for german ocr/cleaning with ocrmypdf
        tesseract-ocr \
        tesseract-ocr-deu \
        ocrmypdf \
        img2pdf \
        unpaper \
        pngquant \
        # python2 is needed to run the jbig2 -> pdf conversion
        python \
    # build the jbig2 encoder
    && mkdir jbig2 \
    && curl -L https://github.com/agl/jbig2enc/archive/ea6a40a.tar.gz | \
    tar xz -C jbig2 --strip-components=1 \
    && cd jbig2 \
    && ./autogen.sh && ./configure && make && make install \
    && cd .. \
    && rm -rf jbig2

WORKDIR /scripts
ADD ocr.sh zenonids-rome-transcriptions.txt /scripts/
