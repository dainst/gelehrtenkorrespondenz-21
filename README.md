
# Gelehrtenkorrespondenz 2021

A repository for the 2021 work within the Project "Gelehrtenkorrespondenz".

Former repo for the work in 2018: https://github.com/dainst/Gelehrtenkorrespondenz


## Development

The Makefile has docker commands to build and run most parts of the project. (Save for the `ocr` dir which has its own Dockerfile and Readme.)

You can build a docker container and run it with

```shell
make build
make run
```

This exposes a jupyter notebook server for the `src` directory at http://127.0.0.1:8888/

You can run the tests with:

```shell
make test
``

To add a python dependency, put in `requirements.in` and run:

```shell
make generate-requirements
```

## Data Sources

Also see:

* [Confluence Documentation (closed)](http://confluence:8090/pages/viewpage.action?pageId=29786709)


### Data Sources

* Original Metadata entered into __Kalliope__:
    - http://kalliope-verbund.info/de/isil?isil.id=DE-2490
    - http://kalliope-verbund.info/de/isil?isil.id=DE-2322
    - Available as EAD-Data dumps from the above confluence page or in the [cumulus dir](https://cumulus.dainst.org/index.php/s/w2Bc2YwRRrCN6pE)
* This was extracted into the __Zenon__ in three (?) collections:
    - [Archiv der Zentrale (1387 ids)](https://zenon.dainst.org/Record/001548031)
    - [Rom, Manuskripte (13664 ids)](https://zenon.dainst.org/Record/001474332)
    - [Rom, Transkriptionen (71 ids)](https://zenon.dainst.org/Record/000880085)
    - A Zenon dump of all linked entries is also in the [cumulus dir](https://cumulus.dainst.org/index.php/s/w2Bc2YwRRrCN6pE)
* Data was added to the Arachne Table `buch`, example SQL:
    - `SELECT bibid, Verzeichnis FROM buch WHERE ArbeitsnotizBuch LIKE '%elehrtenbrief%' LIMIT 10`
    - The field `Verzeichnis` has the folder name in `archaeocloud/S-Arachne/TeiDocuments` where transcriptions are stored (folder name derived from the Zenon id)


### `data/`

* OCR texts for the Rome transcriptions are in [`data/texts`](data/texts), this is the new ocr done in 2021, documented in [`ocr`](ocr)
* TSV files containing all annotations are in [`data/annotations`]. They were created in two steps:
    1. The annotatons done from 2018 onwards on the old ocr were matched to the new OCR as documented [in this script](scripts/docs_match_annotations.sh).
    2. The newly matched annotations were imported into webanno, corrected and exported again to be used in this repo. Documentation [in this script](scripts/docs_extract_annotations.sh)


### Cumulus

The cumulus dir for this project is at

* https://cumulus.dainst.org/index.php/s/w2Bc2YwRRrCN6pE

It contains bigger archive files not suitable for the repo like EAD and webanno exports.
