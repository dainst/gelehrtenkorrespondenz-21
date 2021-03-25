#!/usr/bin/env python3

import argparse
import difflib
import logging
import os
from pathlib import Path
from typing import List, TypeVar, Sequence, Union

from nltk.data import load as nltk_load
from nltk.tokenize import word_tokenize

from data_access import util
from data_access.webanno_tsv import webanno_tsv_read, Annotation, Document, Token

T = TypeVar('T')

logger = logging.getLogger(__file__)

OCR_PAGE_SEP = "\f"

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


def exact_match(annotation: Annotation, tokens: List[Token]) -> Sequence[Token]:
    texts = [t.text for t in tokens]
    idx = util.find_subsequence(texts, annotation.token_texts)
    if idx >= 0:
        return tokens[idx:idx + len(annotation.token_texts)]
    return []


def inexact_match(annotation: Annotation, tokens: List[Token], cutoff=0.75) -> Sequence[Token]:
    lengths = [len(annotation.tokens) + i for i in [-2, -1, 0, 1, 2, 3]]
    token_sequences = util.subsequences_of_length(tokens, *lengths)
    candidates = [''.join(token.text for token in s) for s in token_sequences]
    words = ''.join(annotation.token_texts)
    matches = difflib.get_close_matches(words, candidates, 1, cutoff)
    if matches:
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


def copy_annotation(source: Annotation, targets: List[Token]):
    for target in targets:
        annotation = Annotation(token=target, span_type=source.span_type, label=source.label, label_id=source.label_id)
        target.doc.add_annotation(annotation)


def copy_annotations(doc_with_annotations: Document, other: Document) -> (int, int, int):
    high_confidence = 0
    lower_confidence = 0
    not_found = 0

    tokens_with = doc_with_annotations.tokens
    tokens_without = other.tokens
    diff = len(tokens_without) - len(tokens_with)

    for annotation in doc_with_annotations.annotations_with_type('named_entity'):

        t_start = tokens_with.index(annotation.tokens[0])
        t_start += int(diff / 2)  # correct for the difference in token length
        t_end = t_start + len(annotation.tokens)

        def slice_candidates(half_window: int):
            s = max(0, t_start - half_window)
            e = min(len(tokens_without), t_end + half_window)
            return tokens_without[s:e]

        tokens = []

        # these are matches with a high probability of being correct (high cutoff and near the intended area)
        window_sizes = [(0, 3), (8, 20)]
        for exact_size, inexact_size in window_sizes:
            tokens = exact_match(annotation, slice_candidates(exact_size))
            if tokens:
                high_confidence += 1
                break

            tokens = inexact_match(annotation, slice_candidates(inexact_size), 0.8)
            if tokens:
                high_confidence += 1
                break

        # these are matches with a lower degree of probability (lower cutoff, somewhat more far from intended area)
        sizes_cutoffs = [(3, 0.72), (3, 0.65), (8, 0.72), (8, 0.65), (20, 0.72), (20, 0.65), (40, 0.75)]
        if not tokens:
            for size, cutoff in sizes_cutoffs:
                tokens = inexact_match(annotation, slice_candidates(size), cutoff)
                if tokens:
                    logger.debug('LOW: %s -> %s' % (annotation.text, ' '.join(t.text for t in tokens)))
                    lower_confidence += 1
                    break

        if tokens:
            copy_annotation(annotation, tokens)
        else:
            logger.debug('NO MATCH: %s \n--> %s' % (annotation.text, ' '.join(c.text for c in slice_candidates(20))))
            not_found += 1

    return high_confidence, lower_confidence, not_found


def main(args):
    if not os.path.isdir(args.ocr_dir):
        logger.error(f"Not a directory: {args.ocr_dir}")
        exit(1)
    if not os.path.isdir(args.webanno_dir):
        logger.error(f"Not a directory: {args.webanno_dir}")
        exit(1)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    # Keep counts of types of matches
    per_document_counts: List[(str, int, int, int)] = []
    # Iterate the files we know
    for ocr_filename, webanno_glob in FILE_NAMES:

        with open(args.ocr_dir / ocr_filename, mode='r', encoding='utf-8') as f:
            ocr_texts = ocr_page_split(f.read())

        page_paths = webanno_page_paths(args.webanno_dir, webanno_glob, args.annotator)
        webanno_docs: List[Union[Document, None]] = [webanno_tsv_read(f) for f in page_paths]

        if ocr_filename == '000882135.txt':
            webanno_docs = sort_webanno_docs_for_id_882135(webanno_docs)

        # Some ocr pages do not have counterparts in the webanno docs
        # (happens for example if the pages were never annotated)
        for idx in range(len(ocr_texts)):
            if webanno_file_for_idx(page_paths, idx + 1) is None:
                webanno_docs.insert(idx, None)
        assert (len(ocr_texts) == len(webanno_docs))

        # Do the actual matching here
        counts = (0, 0, 0)
        for idx, (ocr_text, webanno_doc) in enumerate(zip(ocr_texts, webanno_docs)):
            if webanno_doc is not None:
                ocr = clean_ocr(ocr_text)
                ocr_doc = webanno_create_document(ocr)
                result = copy_annotations(webanno_doc, ocr_doc)
                counts = (i + j for i, j in zip(counts, result))

                if args.output_dir:
                    # use the webanno export dirname as our filename
                    filename = os.path.basename(os.path.dirname(webanno_doc.original_path))
                    with open(os.path.join(args.output_dir, filename), mode='w', encoding='utf-8') as f:
                        f.write(ocr_doc.tsv())
        per_document_counts.append((webanno_glob, *counts))

    totals = (
        f'SUMS ({sum(a + b + c for _, a, b, c in per_document_counts)})',
        sum(a[1] for a in per_document_counts),
        sum(a[2] for a in per_document_counts),
        sum(a[3] for a in per_document_counts),
    )
    per_document_counts.append(totals)
    for (name, high_confidence, lower_confidence, not_found) in per_document_counts:
        print('% 6d\t% 6d\t% 6d\t%s' % (high_confidence, lower_confidence, not_found, name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotator', type=str,
                        help='Name of the webanno account to use. Will search <account>.tsv in webanno_dir',
                        default='marina')
    parser.add_argument('ocr_dir', type=Path, help='The directory to search ocr .txt files in.')
    parser.add_argument('webanno_dir', type=Path,
                        help='The directory with the unzipped webanno exports from cumulus')
    parser.add_argument('-o', '--output-dir', type=Path,
                        help='If present, write files with the matched output to this directory.')
    parser.add_argument('-d', '--debug', action='store_true', help='Print some debug messages if present.')
    main(parser.parse_args())
