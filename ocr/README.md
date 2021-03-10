
# OCR

OCR on the Rome transcriptions was repeated in 2021 to:

* generate small PDFs usable with the DAI Book Viewer
* improve OCR results for the Text Mining Parts of the project

## Image input

To find all images connect to books from the rome transcriptions:

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
    -P ocr-images/ -i image_list.txt &
```
