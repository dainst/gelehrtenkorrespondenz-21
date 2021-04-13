#!/usr/bin/env python3

import argparse
import glob
import os
import pathlib
import re

from typing import Iterable

from data_access.book_viewer_json import BookViewerJsonBuilder, Kind
from data_access.webanno_tsv import webanno_tsv_read_file, Annotation

TSV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'annotations'))
LAYER = 'webanno.custom.LetterEntity'
FIELD = 'value'
PAGE_NUMBER_RE = re.compile('.*_page([0-9]{3}).tsv$')
LABELS_TO_KINDS = [
    (re.compile('^PER'), Kind.person),
    (re.compile('^PLACE'), Kind.location),
    (re.compile('^DATE'), Kind.timex),
    (re.compile('^(OBJ|ORG|LIT|MISC)'), Kind.keyterm)
]


def parse_page_number(filename: str):
    try:
        return int(PAGE_NUMBER_RE.match(filename).group(1))
    except (TypeError, AttributeError):
        raise ValueError('Not a valid fileneme: %s' % filename)


def convert_annotation(builder: BookViewerJsonBuilder, page_no: int, a: Annotation) -> None:
    kind = next(kind for regex, kind in LABELS_TO_KINDS if regex.match(a.label))
    builder.add_occurence(kind=kind, lemma=a.text, term=a.text, page=page_no)


def convert_file(builder: BookViewerJsonBuilder, path: str):
    document = webanno_tsv_read_file(path)
    page_no = parse_page_number(path)
    for annotation in document.annotations_with_type(LAYER, FIELD):
        convert_annotation(builder, page_no, annotation)


def convert_files(paths: Iterable[str]) -> str:
    builder = BookViewerJsonBuilder()
    for path in paths:
        convert_file(builder, path)
    return builder.to_json()


def write_output(out_dir: str, zenon_id: str, json: str):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f'{zenon_id}.json')
    with open(path, mode='w', encoding='utf-8') as f:
        f.write(json)


def main(args: argparse.Namespace):
    zenon_ids = os.listdir(TSV_DIR)
    ids_with_files = [(zid, glob.glob(os.path.join(TSV_DIR, zid, '*.tsv'))) for zid in zenon_ids]
    for zid, files in ids_with_files:
        json = convert_files(files)
        write_output(args.out_dir, zid, json)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('out_dir', type=pathlib.Path, help='The directory to write the output files to')
    main(parser.parse_args())
