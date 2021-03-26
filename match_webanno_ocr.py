#!/usr/bin/env python3

import argparse
import difflib
import logging
import os
from pathlib import Path
from typing import List, TypeVar, Sequence

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

EMPTY_DOC = Document()


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


def exact_match(needle: List[Token], haystack: List[Token]) -> Sequence[Token]:
    idx = util.find_subsequence([t.text for t in haystack], [t.text for t in needle])
    if idx >= 0:
        return haystack[idx:idx + len(needle)]
    return []


def inexact_match(needle: List[Token], haystack: List[Token], cutoff=0.75) -> Sequence[Token]:
    lengths = [len(needle) + i for i in [-2, -1, 0, 1, 2, 3]]
    token_sequences = util.subsequences_of_length(haystack, *lengths)
    candidates = [''.join(token.text for token in s) for s in token_sequences]
    matches = difflib.get_close_matches(''.join(t.text for t in needle), candidates, 1, cutoff)
    if matches:
        return token_sequences[candidates.index(matches[0])]
    return []


def match_between(before: List[Token], after: List[Token], candidates: List[Token]):
    match_before = inexact_match(before, candidates)
    if match_before:
        idx_last = candidates.index(match_before[-1])
        candidates_after = candidates[(idx_last + 1):]
        match_after = inexact_match(after, candidates_after)
        if match_after:
            return candidates_after[0:candidates_after.index(match_after[0])]
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


def reorder_documents_for_fit(docs1: List[Document], docs2: List[Document], min_ratio=0.2, text_len=600):
    """
    Attempt to correct wrong page order by matching beginnings of documents.
    Returns two new lists with the second one reordered for better matching the first.
    NOTE: This does not reorder a whole lot of documents, but prevents a lot of errors in those.
    """
    assert (len(docs1) == len(docs2))
    candidates = []
    for idx, (d1, d2) in enumerate(zip(docs1, docs2)):
        ratio = difflib.SequenceMatcher(None, d1.text[:text_len], d2.text[:text_len]).ratio()
        if ratio < min_ratio and docs1[idx] != EMPTY_DOC and docs2[idx] != EMPTY_DOC:
            candidates.append(idx)

    copy_docs2 = list(docs2)
    while candidates:
        idx1 = candidates.pop()
        texts = [docs2[idx2].text[:text_len] for idx2 in candidates]
        match: List[str] = difflib.get_close_matches(docs1[idx1].text[:text_len], texts, 1, min_ratio)
        if match:
            idx_match = candidates[texts.index(match[0])]
            candidates.remove(idx_match)
            copy_docs2[idx1] = docs2[idx_match]

    return list(docs1), copy_docs2


def print_no_match_information(annotation: Annotation):
    filename = os.path.split(os.path.split(annotation.doc.original_path)[0])[1]
    print('-----')
    print('FILE: %s' % filename)
    print('LINE: %d' % annotation.sentences[0].idx)
    print('TEXT: "%s"' % annotation.text)
    print('TYPE: %s' % annotation.label)
    print('CONTEXT:')
    tokens = [t for s in annotation.sentences for t in s.tokens]

    def print_tokens(ts: List[Token]):
        underline = ' '.join(['^' * len(t.text) if t in annotation.tokens else ' ' * len(t.text) for t in ts])
        print(' '.join(t.text for t in ts))
        if underline.strip():
            print(underline)

    line = []
    while tokens:
        token = tokens.pop(0)
        if sum(len(t.text) + 1 for t in line) + len(token.text) > 120:
            print_tokens(line)
            line = []
        line.append(token)
    print_tokens(line)


def copy_annotations(doc_with_annotations: Document, other: Document, print_no_match=False) -> (int, int, int):
    high_confidence = 0
    lower_confidence = 0
    not_found = 0

    tokens_with = doc_with_annotations.tokens
    tokens_without = other.tokens
    diff = len(tokens_without) - len(tokens_with)

    for annotation in doc_with_annotations.annotations_with_type('named_entity'):

        anno_start = tokens_with.index(annotation.tokens[0])
        anno_stop = anno_start + len(annotation.tokens)
        lookup_start = anno_start + int(diff / 2)  # correct for the difference in token length
        lookup_stop = lookup_start + len(annotation.tokens)

        def slice_candidates(half_window: int):
            s = max(0, lookup_start - half_window)
            e = min(len(tokens_without), lookup_stop + half_window)
            return tokens_without[s:e]

        tokens = []

        # these are matches with a high probability of being correct (high cutoff and near the intended area)
        window_sizes = [(0, 3), (8, 20)]
        for exact_size, inexact_size in window_sizes:
            tokens = exact_match(annotation.tokens, slice_candidates(exact_size))
            if tokens:
                high_confidence += 1
                break
            else:
                tokens = inexact_match(annotation.tokens, slice_candidates(inexact_size), 0.8)
                if tokens:
                    lower_confidence += 1
                    break

        # these are matches with a lower degree of probability (lower cutoff, somewhat more far from intended area)
        sizes_cutoffs = [(3, 0.72), (3, 0.65), (8, 0.72), (8, 0.65), (20, 0.72), (20, 0.65), (40, 0.75)]
        if not tokens:
            for size, cutoff in sizes_cutoffs:
                tokens = inexact_match(annotation.tokens, slice_candidates(size), cutoff)
                if tokens:
                    logger.debug('LOW: %s -> %s' % (annotation.text, ' '.join(t.text for t in tokens)))
                    lower_confidence += 1
                    break

        # if we have still no matches, try matching text around the annotation
        if not tokens:
            w = 6
            candidates = slice_candidates(40)
            before = tokens_with[max(0, anno_start - w):anno_start]
            after = tokens_with[anno_stop:min(len(tokens_with), anno_stop + w)]
            between = match_between(before, after, candidates)
            if 0 < len(between) < (2 * len(annotation.tokens)):
                tokens = between
                logger.debug('AROUND: %s -> %s' % (annotation.text, ' '.join(t.text for t in tokens)))
                lower_confidence += 1

        if tokens:
            copy_annotation(annotation, tokens)
        else:
            logger.debug('NO MATCH: %s \n--> %s' % (annotation.text, ' '.join(c.text for c in slice_candidates(20))))
            if print_no_match:
                print_no_match_information(annotation)
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
    for ocr_filename, webanno_glob in FILE_NAMES:

        with open(args.ocr_dir / ocr_filename, mode='r', encoding='utf-8') as f:
            ocr_texts = ocr_page_split(f.read())

        page_paths = webanno_page_paths(args.webanno_dir, webanno_glob, args.annotator)
        webanno_docs = [webanno_tsv_read(f) for f in page_paths]

        if ocr_filename == '000882135.txt':
            webanno_docs = sort_webanno_docs_for_id_882135(webanno_docs)

        # Some ocr pages do not have counterparts in the webanno docs
        # (happens for example if the pages were never annotated)
        for idx in range(len(ocr_texts)):
            if webanno_file_for_idx(page_paths, idx + 1) is None:
                webanno_docs.insert(idx, EMPTY_DOC)
        assert (len(ocr_texts) == len(webanno_docs))

        ocr_texts = [clean_ocr(t) for t in ocr_texts]
        ocr_docs = [webanno_create_document(t) for t in ocr_texts]
        ocr_docs, webanno_docs = reorder_documents_for_fit(ocr_docs, webanno_docs)

        counts = (0, 0, 0)
        for idx, (ocr_doc, webanno_doc) in enumerate(zip(ocr_docs, webanno_docs)):
            result = copy_annotations(webanno_doc, ocr_doc, args.print_no_match)
            counts = (i + j for i, j in zip(counts, result))

            if args.output_dir:
                filename = '%s_page%03d.tsv' % (os.path.splitext(ocr_filename)[0], idx + 1)
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
    parser.add_argument('-p', '--print-no-match', action='store_true',
                        help="Print information on non-matching annotations.")
    parser.add_argument('-d', '--debug', action='store_true', help='Print some debug messages if present.')
    main(parser.parse_args())
