
# Import Kalliope -> Arachne

This describes the general process we followed to enrich the existing Arachne Data with Kalliope Data.

The process is described for the Arachne TEST server bogusman02, but was also applied on the live server.

The files needed for this import are kept in the repo or for the ead persons csv [in the project's cumulus dir](https://cumulus.dainst.org/index.php/s/w2Bc2YwRRrCN6pE) below `/live-import` where logs and import statements from the production import are kept as well.

## Backup

Backup all book rows with our "Arbeitsnotiz" in a temporary table which is then exported.

```sql
CREATE TABLE buch_bkp_glk21_kalliope_import LIKE buch;
INSERT INTO buch_bkp_glk21_kalliope_import SELECT * FROM buch WHERE ArbeitsnotizBuch LIKE 'Gelehrtenbrief%';
```

```bash
mysqldump -u arachne -p arachne buch_bkp_glk21_kalliope_import > buch_bkp_glk21_kalliope_import.sql
```

```sql
DROP TABLE buch_bkp_glk21_kalliope_import;
```

## Import Person data from GND

Create a config for the database to import into:

```
$ cat arachne.TEST.cnf
[client]
host=bogusman02.dai-cloud.uni-koeln.de
user=arachne
password=[...]
database=arachne
default-character-set=utf8
```

Create some urls for which we know the person:

```
mysql -uarachne -p -h bogusman02.dai-cloud.uni-koeln.de arachne < scripts/arachne_set_some_person_uris.sql
```

Import the GND data into arachne based on a list of gnd ids for persons.

```
cat personen-ead.csv | grep '^GND' | cut -d';' -f2 | \
    xargs scripts/arachne_import_from_gnd.py --facts-dir /tmp/entity-facts --db-config arachne.TEST.cnf
```

## Main import

Generate import statements:

```bash
src/arachne_update_by_ead.py ~/Projekte/gelehrtenbriefe/ead/*.xml -o /tmp/updates.sql
scp /tmp/updates.sql bogusman02:updates-glk21-kalliope-import.sql
```

On the remote:

```bash
mysql -uarachne -p arachne < updates-glk21-kalliope-import.sql > updates-glk21-kalliope-import.log
```

On the test server, we need to re-create the SemanticConnection table and trigger indexing (via the frontend GUI, Log In, then choose "Dataimport").

```bash
php /usr/local/ArachneScripts/Automation/SemanticConnection/FillEntityConnectionTable.php &> semantic-connection.log
```

In production this is done each night automatically.

## Test import numbers

```
SELECT count(*) FROM ortsbezug WHERE Ursprungsinformationen LIKE 'Kalliope-Import-GLK21';
SELECT COUNT(*) FROM personobjekte WHERE Kommentar LIKE 'Kalliope-Import-GLK21%';
SELECT COUNT(*) FROM buch_elemente WHERE KommentarBuchElement LIKE 'Kalliope-Import-GLK21';
SELECT COUNT(*) FROM buch WHERE BuchJahr != '' AND ArbeitsnotizBuch LIKE 'Gelehrtenbrief%';
SELECT COUNT(*) FROM person;
```

Output should be

```
30145
29953
4139
14222
2308
```


## Revert main import

(This does not treat the GND-Import)

To recreate the old status quo insert the tmp table and load changed fields.

```bash
mysql -u root -p arachne < buch_bkp_glk21_kalliope_import.sql
```

```sql
UPDATE buch INNER JOIN buch_bkp_glk21_kalliope_import AS bkp ON buch.PS_BuchID = bkp.PS_BuchID SET
    buch.BuchJahr = bkp.BuchJahr,
    buch.BuchEntstehungszeitraum = bkp.BuchEntstehungszeitraum,
    buch.PubYearStart = bkp.PubYearStart,
    buch.PubYearEnd = bkp.PubYearEnd,
    buch.BuchAuthor = bkp.BuchAuthor,
    buch.BuchWeiterePersonen = bkp.BuchWeiterePersonen;
DROP TABLE buch_bkp_glk21_kalliope_import;
```

Created entries in the `ortsbezug` and `personobjekte` table can be identified by comments:

```sql
DELETE FROM ortsbezug WHERE Ursprungsinformationen LIKE 'Kalliope-Import-GLK21';
DELETE FROM personobjekte WHERE Kommentar LIKE 'Kalliope-Import-GLK21';
DELETE FROM buch_elemente WHERE KommentarBuchElement LIKE 'Kalliope-Import-GLK21';
```
