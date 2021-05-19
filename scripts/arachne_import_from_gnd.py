#!/usr/bin/env python3

import argparse
import json
import os.path
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Union, Sequence

import requests
from mysql.connector import connect, MySQLConnection

import sys
from time import sleep

DEFAULT_DB_CONF = os.path.join(os.path.dirname(__file__), '..', 'Config', 'db.my.cnf')

# This is a selection of values .URLSchema, .PS_URIQuelleID from table URIQuelle.
# Note that gnd (source id 3) is not included here as it is not parsed from the
# gnd response but built directly from user input.
ADDITIONAL_SOURCE_IDS = {
    'http://dbpedia.org/resource/': 1,
    'http://viaf.org/viaf/': 5,
    'http://de.wikipedia.org/wiki/': 7,
    'http://en.wikipedia.org/wiki/': 10
}


@dataclass(frozen=True)
class ArachnePerson:
    forename: str = ''
    surname: str = ''
    gender: str = ''
    description: str = ''
    title: str = ''
    prefix: str = ''
    nationality: str = ''


@dataclass(frozen=True)
class ArachneUri:
    source_id: int
    url: str


def gnd_uri(gnd_id: str) -> str:
    return f'http://d-nb.info/gnd/{gnd_id}'


def arachne_gender_label(gnd_gender_id: Optional[str]) -> str:
    return {'https://d-nb.info/standards/vocab/gnd/gender#male': 'männlich',
            'https://d-nb.info/standards/vocab/gnd/gender#female': 'weiblich'}.get(gnd_gender_id, '')


def insert_person_sql(p: ArachnePerson, working_comment='GND-Import'):
    fields = [
        ('VornameSonst', p.forename),
        ('FamVatersnameSonst', p.surname),
        ('Geschlecht', p.gender),
        ('Kurzbeschreibung', p.description),
        ('Titel', p.title),
        ('Beiname', p.prefix),
        ('EthnieNationalitaet', p.nationality),
        ('ArbeitsnotizPerson', working_comment),
    ]
    fields = [(k, v) for k, v in fields if v]
    updates = [f"{k} = '{v}'" for k, v in fields]
    return 'INSERT INTO person SET ' + ', '.join(updates)


def insert_uri_sql(uri: ArachneUri, person_id: int, relation='sameAs'):
    sql = f"INSERT INTO URI (FS_PersonID, URI, FS_URIQuelleID, Beziehung) VALUES (%d, '%s', %d, '%s')"
    return sql % (person_id, uri.url, uri.source_id, relation)


def db_insert_no_commit(connection: MySQLConnection, sql: str) -> int:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return cursor.lastrowid


def db_insert_person(connection: MySQLConnection, p: ArachnePerson) -> int:
    return db_insert_no_commit(connection, insert_person_sql(p))


def db_insert_uri_if_not_exists(connection: MySQLConnection, uri: ArachneUri, person_id: int) -> int:
    sql = 'SELECT PS_URIID FROM URI WHERE FS_PersonID = %d AND FS_URIQuelleID = %d'
    sql = sql % (person_id, uri.source_id)
    uri_id = db_select_single_val(connection, sql)
    if uri_id:
        return uri_id
    else:
        return db_insert_no_commit(connection, insert_uri_sql(uri, person_id))


def db_select_single_val(connection: MySQLConnection, sql: str, params=()) -> Optional[Union[int, str]]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        try:
            return list(cursor)[0][0]
        except IndexError:
            return None


def db_select_person_id(connection: MySQLConnection, gnd_id: str) -> Optional[int]:
    sql = f'SELECT FS_PersonID FROM URI WHERE URI LIKE "%{gnd_uri(gnd_id)}%"'
    return db_select_single_val(connection, sql)


def parse_person(data: Dict) -> ArachnePerson:
    return ArachnePerson(
        forename=data.get('forename', ''),
        surname=data.get('surname', ''),
        gender=arachne_gender_label(data.get('gender', {}).get('@id', '')),
        description=data.get('biographicalOrHistoricalInformation', ''),
        title=';'.join(t for t in [data.get('titleOfNobility'), data.get('academicDegree')] if t),
        prefix=data.get('prefix', ''),
        nationality=data.get('associatedCountry', [{}])[0].get('preferredName', '')
    )


def parse_uris(data: Dict) -> Sequence[ArachneUri]:
    def lookup_source_id(url: str):
        return next((sid for scheme, sid in ADDITIONAL_SOURCE_IDS.items() if url.startswith(scheme)), None)
    urls = [item.get('@id', '') for item in data.get('sameAs', dict())]
    sids = [lookup_source_id(url) for url in urls]
    return [ArachneUri(sid, url) for url, sid in zip(urls, sids) if sid and url]


def fetch_data_remote(gnd_id: str, save_to: Optional[str] = None) -> str:
    response = requests.get(f'https://hub.culturegraph.org/entityfacts/{gnd_id}')
    sleep(0.5)  # Let's idle a bit in case we hit the API again
    assert response.status_code == 200
    if save_to:
        with open(save_to, mode='w', encoding='utf-8') as f:
            f.write(response.text)
    return response.text


def get_data_local_or_remote(gnd_id: str, facts_dir: Optional[Path]) -> str:
    if facts_dir:
        facts_file = os.path.join(facts_dir, f'{gnd_id}.json')
        if os.path.exists(facts_file):
            with open(facts_file, mode='r', encoding='utf8') as f:
                return f.read()
        else:
            return fetch_data_remote(gnd_id, facts_file)
    else:
        return fetch_data_remote(gnd_id)


def collect_gnd_data(gnd_id: str, facts_dir: Optional[Path]) -> (ArachnePerson, Sequence[ArachneUri]):
    raw_data = get_data_local_or_remote(gnd_id, facts_dir)
    data = json.loads(raw_data)
    person = parse_person(data)
    uris = [ArachneUri(3, gnd_uri(gnd_id)), *parse_uris(data)]
    return person, uris


def handle_person(connection: MySQLConnection, facts_dir: Optional[Path], gnd_id: str) -> int:
    person, uris = collect_gnd_data(gnd_id, facts_dir)

    person_id = db_select_person_id(connection, gnd_id)
    if not person_id:
        person_id = db_insert_person(connection, person)

    for uri in uris:
        db_insert_uri_if_not_exists(connection, uri, person_id)

    return person_id


def main(args: argparse.Namespace):
    with connect(option_files=args.db_config) as connection:
        for gnd_id in args.gnd_ids:
            person_id = handle_person(connection, args.facts_dir, gnd_id)
            connection.commit()
            args.out_file.write('%s, %d\n' % (gnd_id, person_id))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Reads gnd ids, imports gnd data to arachne, outputs gnd ids with FS_PersonIDs.')
    parser.add_argument('gnd_ids', type=str, nargs='*', help="GND id(s) to lookup and import")
    parser.add_argument('--facts-dir', type=Path,
                        help='Optional: A directory with <id>.json files to use as a cache for querying the GND.')
    parser.add_argument('--db-config', default=DEFAULT_DB_CONF, type=str,
                        help='An ini-style config file to use for the db connection. '
                             'Expects at least host, database, user, password below a [client] header.')
    parser.add_argument('-o', '--out-file', type=argparse.FileType('w'), default=sys.stdout,
                        help='An output file to write to, default is stdout.')
    main(parser.parse_args())
