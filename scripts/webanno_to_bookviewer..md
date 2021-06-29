
This describes the process of exporting annotations from a webanno project into a bookviewer representation.

Find out your project id by listing projects in the api, then export a zip of the project.

```sh
curl 'http://[webanno-user]:[webanno-pass]@nlp.dainst.org:18080/webanno/api/aero/v1/projects'
curl 'http://[webanno-user]:[webanno-pass]@nlp.dainst.org:18080/webanno/api/aero/v1/projects/34/export.zip' --output /tmp/export.zip
```

The archive contains annotations in files named by the annotator's webanno user (e.g. "marina.tsv").

The original filename is contained in the directory name, so rename these files to that name.

```sh
unzip -d /tmp/export /tmp/export.zip
mkdir /tmp/export-tsvs
find /tmp/export/annotation -name "marina.tsv" | while read f; do cp "$f" "/tmp/export-tsvs/$(basename $(dirname "$f"))"; done
```

Put the tsv files in a directory named by their zenon id (should be contained in the files' name as well).

You can now use the conversion script to generate a bookviewer json files from these exports.

```sh
mkdir /tmp/export-tsvs/[zenonid]
mv /tmp/export-tsvs/*.tsv /tmp/export-tsvs/[zenonid]
src/write_book_viewer_json.py -i /tmp/export-tsvs /tmp
```

To display the annotations, copy the bookviewer file to the test or prod locations, e.g.:

```sh
scp /tmp/[zenonid].json ber-dockerswarmtest01vm:/var/lib/docker/volumes/bookviewer_data/_data/gelehrtenbriefe/annotations/
scp /tmp/[zenonid].json ber-dockerswarm01vm:/var/lib/docker/volumes/bookviewer_data/_data/gelehrtenbriefe/annotations/
```

You should now see the annotations at:

* https://viewer.test.idai.world/?file=data/gelehrtenbriefe/[zenonid].pdf&pubid=annotations/[zenonid].json
* https://viewer.idai.world/?file=data/gelehrtenbriefe/[zenonid].pdf&pubid=annotations/[zenonid].json
