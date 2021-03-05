
# Gelehrtenkorrespondenz 2021

A repository for the 2021 work within the Project "Gelehrtenkorrespondenz".

Former repo for the work in 2018: https://github.com/dainst/Gelehrtenkorrespondenz


## Development

### Run Tests

```shell
python -m unittest test/webanno_tsv_test.py
```

### Extract webanno archives:

1. Download `webanno-exports-zip` from [Cumulus](https://cumulus.dainst.org/index.php/s/w2Bc2YwRRrCN6pE)
2. Extract and prepare the files by running `data_access/webanno_prepare_files.sh webanno-exports-zip some/target/dir`


## Data Sources

Also see:

* [Confluence Documentation (closed)](http://confluence:8090/pages/viewpage.action?pageId=29786709)

Most data is:

* At the cumulus dir for this project: https://cumulus.dainst.org/index.php/s/w2Bc2YwRRrCN6pE
* In the directory with this README (see below for details)

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

* OCR texts for the Rome transcriptions is in `transcriptions_texts`
* From the folders `archaeocloud/S-Arachne/TeiDocuments` (see above):
    - There are `transcription.xml` files for 9929 of the Zenon entries.
    - Only 69 of them have text data (OCR). The text was extracted with an xpath command and leading whitespace was removed

        `ls transcriptions | while read f; do xidel -e '//text' "transcriptions/${f}" | sed 's/^\s*//g' > transcriptions_texts/$(basename -s.xml "$f").txt; done`

### Some statistics

For the 69 records contained in `transcriptions_texts`

```
#sentences      211093
#words         4102482
mean(words/s)       19.43
stdev(words/s)      17.04
```

Main detected languages (with number of sentences):

```
 ('fr', 526),
 ('nl', 619),
 ('lb', 1822),
 ('it', 3447),
 ('en', 17658),
 ('de', 182365)
```