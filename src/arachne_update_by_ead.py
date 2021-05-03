#!/usr/bin/env python3

import argparse
import os.path
import sys
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence

from MySQLdb import escape_string

from data_access.ead_xml import read_components_from_file, parse_unitdate, Component, ParsedDate

RESOURCE_DIR = os.path.join(os.path.dirname(__file__), 'resources')
ZENON_KALLIOPE_IDS_FILE = os.path.join(RESOURCE_DIR, 'zenonids_to_kalliope_ids.csv')
GND_GAZETTEER_IDS_FILE = os.path.join(RESOURCE_DIR, 'geo-gnd-to-gazetteer-ids')

ACCEPTED_PERSON_ROLES = {'Adressat', 'Behandelt', 'Bestandsbildner', 'Erwähnt', 'Dokumentiert'}
ACCEPTED_AUTHOR_ROLES = {'Verfasser'}


@dataclass(frozen=True)
class ArachneData:
    zenon_id: str = ''
    start_date: Optional[ParsedDate] = None
    end_date: Optional[ParsedDate] = None
    author_name: str = ''
    other_names: Sequence[str] = field(default_factory=list)
    gaz_ids_thematic: Sequence[str] = field(default_factory=list)


def str_val(s: str):
    return "'%s'" % escape_string(s).decode('utf8')


def parse_resource_file(path: str, key_idx=0, val_idx=1, delim='\t') -> Dict[str, str]:
    with open(path, 'r') as f:
        ids = [line.split(delim) for line in f.readlines()]
    min_len = max(key_idx, val_idx) + 1
    return {t[key_idx].strip(): t[val_idx].strip() for t in ids if len(t) >= min_len}


def parse_gnd_to_gazetteer_id_map() -> Dict[str, str]:
    return parse_resource_file(GND_GAZETTEER_IDS_FILE, key_idx=1, val_idx=2, delim=';')


def parse_kalliope_to_zenon_id_map() -> Dict[str, str]:
    return parse_resource_file(ZENON_KALLIOPE_IDS_FILE, key_idx=1, val_idx=0)


def convert_arachne_data(component: Component,
                         kalliope_to_zenon: Dict[str, str], gnd_to_gaz: Dict[str, str]) -> ArachneData:
    args = {'zenon_id': kalliope_to_zenon.get(component.ead_id)}

    if component.unitdate:
        args['start_date'], args['end_date'] = parse_unitdate(component.unitdate)

    if component.persons:
        args['author_name'] = next((p.normal for p in component.persons if p.role in ACCEPTED_AUTHOR_ROLES), '')
        args['other_names'] = [p.normal for p in component.persons if p.role in ACCEPTED_PERSON_ROLES]

    if component.places:
        args['gaz_ids_thematic'] = [gnd_to_gaz[p.auth_file_number] for p in component.places if p.source == 'GND']

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
        eqls.append(('BuchPubYearStart', ar.start_date.year))
        eqls.append(('BuchPubYearEnd', ar.end_date.year))
    if ar.author_name:
        eqls.append(('BuchAuthor', ar.author_name))
    if ar.other_names:
        eqls.append(('BuchWeiterePersonen', '; '.join(ar.other_names)))
    if eqls:
        strs = [f"{key} = {str_val(val)}" for key, val in eqls]
        return f"UPDATE buch SET {', '.join(strs)} WHERE bibid = {ar.zenon_id};"
    return ""


def gather_statements(arachne_data: ArachneData) -> Sequence[str]:
    if not arachne_data.zenon_id:
        return []
    return [
        update_buch_statement(arachne_data)
    ]


def main(args: argparse.Namespace):
    zenonid_map = parse_kalliope_to_zenon_id_map()
    gazetteerid_map = parse_gnd_to_gazetteer_id_map()
    for path in args.ead_xml_files:
        for c in read_components_from_file(path):
            arachne_data = convert_arachne_data(c, zenonid_map, gazetteerid_map)
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
