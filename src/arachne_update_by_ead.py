#!/usr/bin/env python3

import argparse
import os.path
import sys
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence

from MySQLdb import escape_string

from data_access.ead_xml import (
    read_components_from_file, parse_addressee_place, parse_unitdate,
    Component, ParsedDate, Place
)

RESOURCE_DIR = os.path.join(os.path.dirname(__file__), 'resources')
ZENON_KALLIOPE_IDS_FILE = os.path.join(RESOURCE_DIR, 'zenonids_to_kalliope_ids.csv')
GND_GAZETTEER_IDS_FILE = os.path.join(RESOURCE_DIR, 'geo-gnd-to-gazetteer-ids.csv')
DE611_GAZETTEER_IDS_FILE = os.path.join(RESOURCE_DIR, 'geo-de611-to-gazetteer-ids.csv')

ACCEPTED_PERSON_ROLES = {'Adressat'}
ACCEPTED_AUTHOR_ROLES = {'Verfasser'}


@dataclass(frozen=True)
class ArachneData:
    zenon_id: str = ''
    start_date: Optional[ParsedDate] = None
    end_date: Optional[ParsedDate] = None
    author_name: str = ''
    other_names: Sequence[str] = field(default_factory=list)
    gaz_ids_thematic: Sequence[str] = field(default_factory=list)


@dataclass(frozen=True)
class GazetteerIdLookupDicts:
    by_gnd: Dict[str, str]
    by_de611: Dict[str, str]
    by_name: Dict[str, str]


def str_val(s: str):
    return "'%s'" % escape_string(s).decode('utf8')


def parse_resource_file(path: str, key_idx=0, val_idx=1, delim='\t') -> Dict[str, str]:
    with open(path, 'r') as f:
        ids = [line.split(delim) for line in f.readlines()]
    min_len = max(key_idx, val_idx) + 1
    return {t[key_idx].strip(): t[val_idx].strip() for t in ids if len(t) >= min_len}


def parse_kalliope_to_zenon_id_map() -> Dict[str, str]:
    return parse_resource_file(ZENON_KALLIOPE_IDS_FILE, key_idx=1, val_idx=0)


def parse_names_to_gazetteer_id_resource_file() -> Dict[str, str]:
    from_gnd = parse_resource_file(GND_GAZETTEER_IDS_FILE, key_idx=0, val_idx=2, delim=';')
    from_de611 = parse_resource_file(DE611_GAZETTEER_IDS_FILE, key_idx=0, val_idx=2, delim=';')
    return {**from_de611, **from_gnd}


def parse_gazetteer_id_lookup_dicts() -> GazetteerIdLookupDicts:
    return GazetteerIdLookupDicts(
        by_gnd=parse_resource_file(GND_GAZETTEER_IDS_FILE, key_idx=1, val_idx=2, delim=';'),
        by_de611=parse_resource_file(DE611_GAZETTEER_IDS_FILE, key_idx=1, val_idx=2, delim=';'),
        by_name=parse_names_to_gazetteer_id_resource_file()
    )


def lookup_gazetteer_id(place: Place, gaz_ids_lookup: GazetteerIdLookupDicts) -> Optional[str]:
    if place.source == 'GND':
        return gaz_ids_lookup.by_gnd[place.auth_file_number]
    elif place.source == 'DE-611':
        return gaz_ids_lookup.by_de611[place.auth_file_number]
    else:
        return gaz_ids_lookup.by_name.get(place.normal, None)


def lookup_thematic_place_ids(component: Component, gaz_ids_lookup: GazetteerIdLookupDicts) -> [str]:
    places = list(component.plac es)
    if component.note:
        # the component's note field may contain an "Empfängerort" entered as free text
        places.append(parse_addressee_place(component.note.text))
    gazetteer_ids = [lookup_gazetteer_id(p, gaz_ids_lookup) for p in places if p]
    return [gid for gid in gazetteer_ids if gid]


def convert_arachne_data(component: Component,
                         kalliope_to_zenon: Dict[str, str], gaz_id_lookup: GazetteerIdLookupDicts) -> ArachneData:
    args = {'zenon_id': kalliope_to_zenon.get(component.ead_id)}

    if component.unitdate:
        args['start_date'], args['end_date'] = parse_unitdate(component.unitdate)

    if component.persons:
        args['author_name'] = next((p.normal for p in component.persons if p.role in ACCEPTED_AUTHOR_ROLES), '')
        args['other_names'] = [p.normal for p in component.persons if p.role in ACCEPTED_PERSON_ROLES]

    args['gaz_ids_thematic'] = lookup_thematic_place_ids(component, gaz_id_lookup)

    return ArachneData(**args)


def format_book_creation_time(start: ParsedDate, end: Optional[ParsedDate]) -> str:
    def format_single(d: ParsedDate):
        numbers = [d.day, d.month, d.year]
        return '.'.join(n for n in numbers if n)

    return ' - '.join(format_single(date) for date in [start, end] if date)


def update_buch_statement(ar: ArachneData) -> str:
    eqls = []
    if ar.start_date:
        eqls.append(('BuchJahr', ar.start_date.year))
        eqls.append(('BuchEntstehungszeitraum', format_book_creation_time(ar.start_date, ar.end_date)))
    if ar.start_date and ar.end_date and ar.start_date.year != ar.end_date.year:
        eqls.append(('PubYearStart', ar.start_date.year))
        eqls.append(('PubYearEnd', ar.end_date.year))
    if ar.author_name:
        eqls.append(('BuchAuthor', ar.author_name))
    if ar.other_names:
        eqls.append(('BuchWeiterePersonen', '; '.join(ar.other_names)))
    if eqls:
        strs = [f"{key} = {str_val(val)}" for key, val in eqls]
        return f"UPDATE buch SET {', '.join(strs)} WHERE bibid = {ar.zenon_id};"
    return ""


def create_ortsbezug_if_not_exists_stmt(gazetteer_id: str, zenon_id: str, type_ortsbezug="thematischer Ort") -> str:
    set_var_place = 'SELECT @place_id := PS_OrtID from ort where ort.Gazetteerid = %s LIMIT 1' % gazetteer_id
    set_var_book = 'SELECT @book_id := PS_BuchID from buch where buch.bibid = %s' % zenon_id
    insert = 'INSERT INTO ortsbezug (FS_OrtID, FS_BuchID, ArtOrtsangabe, Ursprungsinformationen)'
    insert += " SELECT @place_id, @book_id , '%s', 'Kalliope-Import-GLK21' FROM ortsbezug" % type_ortsbezug
    insert += ' WHERE (FS_BuchID = @book_id AND FS_OrtID = @place_id AND ArtOrtsangabe = \'%s\')' % type_ortsbezug
    insert += ' HAVING COUNT(*) = 0 AND @place_id IS NOT NULL AND @book_id IS NOT NULL'
    reset_vars = 'SELECT @place_id := NULL, @book_id := NULL'
    return '; '.join([set_var_place, set_var_book, insert, reset_vars, ''])


def create_ortsbezug_statements(ar: ArachneData) -> Sequence[str]:
    return [create_ortsbezug_if_not_exists_stmt(gid, ar.zenon_id) for gid in ar.gaz_ids_thematic if gid]


def gather_statements(arachne_data: ArachneData) -> Sequence[str]:
    if not arachne_data.zenon_id:
        return []
    return [
        update_buch_statement(arachne_data),
        *create_ortsbezug_statements(arachne_data)
    ]


def main(args: argparse.Namespace):
    zenonid_map = parse_kalliope_to_zenon_id_map()
    gazetteer_id_dicts = parse_gazetteer_id_lookup_dicts()
    for path in args.ead_xml_files:
        for c in read_components_from_file(path):
            arachne_data = convert_arachne_data(c, zenonid_map, gazetteer_id_dicts)
            for stmt in gather_statements(arachne_data):
                if stmt:
                    args.out_file.write(stmt)
                    args.out_file.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ead_xml_files', nargs='*', help="The xml files from kalliope's ead output to parse.")
    parser.add_argument('-o', '--out_file', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help="The output file to write SQL statements to. Defaults to stdout.")
    main(parser.parse_args())
