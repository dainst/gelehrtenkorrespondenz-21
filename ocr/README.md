
# OCR

OCR on the Rome transcriptions was repeated in 2021 to:

* generate small PDFs usable with the DAI Book Viewer
* improve OCR results

## Image input

To find all images connected to books from the rome transcriptions:

1. Use an SQL snippet to generate an Image URL list from Arachne
2. Curl the images to use them locally

```bash
mysql -uarachne -p \
    -h bogusman01.dai-cloud.uni-koeln.de \
    -N \
    arachne \
    < fetch_image_list.sql > image_list.txt
wget --no-verbose \
    -o image_fetch.log \
    --wait=1 \
    -P ocr-images/ -i image_list.txt
```

## Image Compression and OCR

Use the Dockerfile at `ocr/Dockerfile` to build an image with all necessary dependencies.

Given that the input images are at `~/ocr/images` and output should be at `~/ocr/out`, you can use the following to run the OCR process (Existing files will not be run again.):

```bash
docker build --tag gelehrtenbriefe-ocr ocr/
docker run -it --rm \
    --volume ~/ocr:/data \
    gelehrtenbriefe-ocr \
    /scripts/ocr.sh /scripts/zenonids-rome-transcriptions.txt /data/images /data/out
```
