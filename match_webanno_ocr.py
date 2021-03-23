#!/usr/bin/env python3

import argparse
import csv
import difflib
import logging
import os
import re
from pathlib import Path
from typing import Iterator, List, TypeVar, Sequence

from nltk.data import load as nltk_load
from nltk.tokenize import word_tokenize

from data_access import util
from data_access.webanno_tsv import webanno_tsv_read, Annotation, Document, Sentence, Token

T = TypeVar('T')

logger = logging.getLogger(__file__)

OCR_PAGE_SEP = "\f"

WEBANNO_COMMENT_RE = re.compile('^#')
WEBANNO_FIELDS = ['sent_tok_idx', 'offset', 'token', 'pos', 'lemma', 'entity_id', 'named_entity']

RESOURCE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data_access', 'resources')
SENTENCE_TOKENIZER_PICKLE = os.path.join(RESOURCE_DIR, 'dai_german_punkt.pickle')
sentence_tokenizer = nltk_load(SENTENCE_TOKENIZER_PICKLE)

# teach the sentence tokenizer to not break on month days
sentence_tokenizer._params.abbrev_types.update(map(str, range(1, 32)))

FILE_NAMES = [
    # ('000880098.txt', 'Gelehrtekorrespondenz_Test_2021-02-03_1432/annotation/1.Braun_an_Gerhard1832-35_page*'),

    ('001313708.txt', '11_BOOK-ZID1313708_2021-02-03_1354/annotation/11_BOOK-ZID1313708_page*'),
    ('000882135.txt', '16_BOOK-ZID882135_2021-02-03_1442/annotation/16_BOOK-ZID882135_page*'),
    ('000884476.txt', '25_BOOK-ZID884476_2021-02-03_1443/annotation/25_BOOK-ZID884476_page*'),
    ('000884487.txt', '26_BOOK-ZID884487_2021-02-03_1444/annotation/26_BOOK-ZID884487_page*'),
    ('000884345.txt', '34_BOOK-ZID884345_2021-02-03_1445/annotation/34_BOOK-ZID884345_page*'),
    ('000884500.txt', '68_BOOK-ZID884500_2021-02-03_1445/annotation/68_BOOK-ZID884500_page*'),
    ('000882126.txt', 'Gelehrtekorrespondenz_Test_2021-02-03_1432/annotation/2.Braun1835_page*'),
    ('000884002.txt', 'Gelehrtekorrespondenz_Test_2021-02-03_1432/annotation/3.Brunn1858_page*'),
    ('001315095.txt', 'Gelehrtekorrespondenz_Test_2021-02-03_1432/annotation/4_MommsenAnBrunn_page*'),
    ('000884517.txt', 'Gelehrtekorrespondenz_Test_2021-02-03_1432/annotation/5_GerhardAnBraun1844-1856_page*'),
    ('001314449.txt', 'Gelehrtekorrespondenz_Test_2021-02-03_1432/annotation/6_HenzenAnGerhard_page*'),
    ('001313974.txt', 'Gelehrtekorrespondenz_Test_2021-02-03_1432/annotation/7_HelbigAnHenzen1863_page*'),
    ('001315090.txt', 'Gelehrtekorrespondenz_Test_2021-02-03_1432/annotation/8_LepsiusAnHenzen-Helbig1872-1884_page*'),
    ('001313719.txt', 'Gelehrtekorrespondenz_Test_2021-02-03_1432/annotation/9_GerhardAnHenzen1843-1850_page*'),
]


def webanno_page_paths(export_dir: Path, page_glob: str, annotator: str) -> List[Path]:
    path_glob_in_dir = os.path.join(page_glob, annotator + '.tsv')
    paths = export_dir.glob(path_glob_in_dir)
    return sorted(paths)


def ocr_page_split(ocr_text: str) -> [str]:
    return ocr_text.split(OCR_PAGE_SEP)


def webanno_parse_file(path: str) -> [dict]:
    with open(path) as f:
        uncommented = [line for line in f.readlines() if not re.match(WEBANNO_COMMENT_RE, line)]
    return csv.DictReader(uncommented, dialect='excel-tab', fieldnames=WEBANNO_FIELDS)


def webanno_file_for_idx(paths: List[Path], index: int):
    # webanno files have the 0-padded page number in the file name
    idx_str = "_page%03d" % index
    paths = [p for p in paths if idx_str in str(p)]
    assert (len(paths) <= 1)
    return paths[0] if len(paths) == 1 else None


def clean_ocr(text: str) -> str:
    return '\n'.join(util.remove_hyphenation(text.split('\n')))


def webanno_create_document(text: str) -> Document:
    doc = Document([])
    sentences = sentence_tokenizer.tokenize(text, realign_boundaries=True)
    for sentence in sentences:
        words = word_tokenize(sentence, 'german')
        doc.add_tokens_as_sentence(words)
    return doc


def sentences_near(sentences: Sequence[Sentence], index: int, window=5) -> Iterator[Sentence]:
    start_idx = min(index, len(sentences) - 1)  # if index is too big, return at least some items at the end
    for sentence in util.items_around(sentences, start_idx, window):
        yield sentence


def exact_match(annotation: Annotation, sentence: Sentence) -> Sequence[Token]:
    idx = util.find_subsequence(sentence.token_texts, annotation.token_texts)
    if idx >= 0:
        return sentence.tokens[idx:idx + len(annotation.token_texts)]
    return []


def inexact_match(annotation: Annotation, sentence: Sentence, cutoff=0.75) -> Sequence[Token]:
    lengths = [len(annotation.tokens) + i for i in [-2, -1, 0, 1, 2, 3]]
    token_sequences = util.subsequences_of_length(sentence.tokens, *lengths)
    candidates = [''.join(token.text for token in s) for s in token_sequences]
    words = ''.join(annotation.token_texts)
    matches = difflib.get_close_matches(words, candidates, 1, cutoff)
    if len(matches) > 0:
        return token_sequences[candidates.index(matches[0])]
    return []


def sort_webanno_docs_for_id_882135(webanno_docs):
    # this book had an error in how the original ocr was sorted
    # (page numbers were erroneously str sorted: 1, 10, 11, …, 100, … 199, 2, 21, … )
    new_webanno = []
    orig_ocr_order = list(map(int, sorted(map(str, range(1, len(webanno_docs) + 1)))))
    for i in range(0, len(webanno_docs)):
        idx = orig_ocr_order.index(i + 1)
        new_webanno.append(webanno_docs[idx])
    return new_webanno


def copy_annotations(doc_with_annotations: Document, other: Document):
    found_exact = 0
    found_approx = 0
    not_found = 0

    for sent_i, sentence in enumerate(doc_with_annotations.sentences):

        for annotation in sentence.annotations_with_type('named_entity'):
            fit = False
            tokens = []

            # Try an exact fit looking at this sentence and the surrounding ones
            if not fit:
                for other_sentence in sentences_near(other.sentences, sent_i, window=2):
                    tokens = exact_match(annotation, other_sentence)
                    if len(tokens) > 0:
                        found_exact += 1
                        fit = True
                        break

            # Try an inexact fit by matching to the nearest best sequence
            if not fit:
                for other_sentence in sentences_near(other.sentences, sent_i, window=5):
                    tokens = inexact_match(annotation, other_sentence, 0.75)
                    if len(tokens) > 0:
                        found_approx += 1
                        fit = True
                        break

            # if there is no fit and the annotation is very short and the sentence not very short,
            # then try matching the complete sentence first, then repeat the inexact match with a lower cutoff.
            if not fit \
                    and (sum(len(w) for w in annotation.token_texts) <= 15) \
                    and len(sentence.tokens) > (2 * len(annotation.tokens)):
                others = [s.text for s in other.sentences]
                matches = difflib.get_close_matches(annotation.sentence.text, others, 1, 0.4)
                if len(matches) > 0:
                    matched = [s for s in other.sentences if s.text == matches[0]][0]
                    tokens = inexact_match(annotation, matched, 0.6)
                    if len(tokens) > 0:
                        found_approx += 1
                        fit = True

            if not fit:
                not_found += 1

    return found_exact, found_approx, not_found


def main(args):
    if not os.path.isdir(args.ocr_dir):
        logger.error(f"Not a directory: {args.ocr_dir}")
        exit(1)
    if not os.path.isdir(args.webanno_dir):
        logger.error(f"Not a directory: {args.webanno_dir}")
        exit(1)

    # Keep counts of types of matches
    per_document_counts = []
    # Iterate the files we know
    for ocr_filename, webanno_glob in FILE_NAMES:

        with open(args.ocr_dir / ocr_filename, mode='r', encoding='utf-8') as f:
            ocr_texts = ocr_page_split(f.read())

        page_paths = webanno_page_paths(args.webanno_dir, webanno_glob, args.annotator)
        webanno_docs = [webanno_tsv_read(f) for f in page_paths]

        if ocr_filename == '000882135.txt':
            webanno_docs = sort_webanno_docs_for_id_882135(webanno_docs)

        # Some ocr pages do not have counterparts in the webanno docs
        to_delete = []
        for idx in range(len(ocr_texts)):
            if webanno_file_for_idx(page_paths, idx + 1) is None:
                to_delete.append(idx)
        for idx in sorted(to_delete, reverse=True):
            del ocr_texts[idx]
        assert (len(ocr_texts) == len(webanno_docs))

        # Do the actual matching here
        counts = (0, 0, 0)
        for idx, (ocr_text, webanno_doc) in enumerate(zip(ocr_texts, webanno_docs)):
            if webanno_doc is not None:
                ocr = clean_ocr(ocr_text)
                ocr_doc = webanno_create_document(ocr)
                result = copy_annotations(webanno_doc, ocr_doc)
                counts = (i + j for i, j in zip(counts, result))

        per_document_counts.append((webanno_glob, *counts))

    totals = (
        'SUMS',
        sum(a[1] for a in per_document_counts),
        sum(a[2] for a in per_document_counts),
        sum(a[3] for a in per_document_counts),
    )
    per_document_counts.append(totals)
    for (name, exact, approx, not_found) in per_document_counts:
        print('% 6d\t% 6d\t% 6d\t%s' % (exact, approx, not_found, name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotator', type=str,
                        help='Name of the webanno account to use. Will search <account>.tsv in webanno_dir',
                        default='marina')
    parser.add_argument('ocr_dir', type=Path, help='The directory to search ocr .txt files in.')
    parser.add_argument('webanno_dir', type=Path,
                        help='The directory with the unzipped webanno exports from cumulus')
    main(parser.parse_args())
