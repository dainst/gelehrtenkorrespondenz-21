import csv
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

NO_LABEL_ID = -1
COMMENT_RE = re.compile('^#')
SENTENCE_RE = re.compile('^#Text=(.*)')
FIELD_EMPTY_RE = re.compile('^[_*]')
FIELD_WITH_ID_RE = re.compile(r'(.*)\[([0-9]*)]$')

TSV_FIELDNAMES = ['sent_tok_idx', 'offsets', 'token', 'pos', 'lemma', 'entity_id', 'named_entity']

logger = logging.getLogger(__file__)

class WebannoTsvDialect(csv.Dialect):
    delimiter = '\t'
    quotechar = None  # disables escaping
    doublequote = False
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_NONE


@dataclass
class Token:
    sentence: 'Sentence'
    idx: int
    start: int
    end: int
    text: str


class Annotation:

    def __init__(self, token: Token, span_type: str, label: str, label_id: int):
        self._tokens = [token]
        self.span_type = span_type
        self.label = label
        self.label_id = label_id

    @property
    def start(self):
        return self._tokens[0].start

    @property
    def end(self):
        return self._tokens[-1].end

    @property
    def sentence(self):
        return self._tokens[0].sentence

    @property
    def text(self):
        return ' '.join([t.text for t in self._tokens])

    @property
    def tokens(self):
        # return a read-only copy
        return list(self._tokens)

    @property
    def token_texts(self):
        return [token.text for token in self._tokens]

    def merge_other(self, other: 'Annotation'):
        assert (self.span_type == other.span_type)
        assert (self.label == other.label)
        assert (self.label_id == other.label_id)
        assert (self.sentence == other.sentence)
        assert ((self.end + 1) == other.start or (other.end + 1) == self.start)
        self._tokens = sorted(self._tokens + other.tokens, key=lambda t: t.start)


class Sentence:
    idx: int
    text: str
    tokens: List[Token]

    def __init__(self, idx: int, text: str):
        self.idx = idx
        self.text = text
        self.tokens = []
        self._annotations: Dict[str, List[Annotation]] = defaultdict(list)

    @property
    def token_texts(self) -> List[str]:
        return [token.text for token in self.tokens]

    def add_annotation(self, annotation: Annotation):
        merged = False
        # check if we should merge with an existing annotation
        if annotation.label_id != NO_LABEL_ID:
            same_type = self.annotations_with_type(annotation.span_type)
            same_id = [a for a in same_type if a.label_id == annotation.label_id]
            assert (len(same_id)) <= 1
            if len(same_id) > 0:
                same_id[0].merge_other(annotation)
                merged = True
        if not merged:
            assert (annotation.sentence == self)
            self._annotations[annotation.span_type].append(annotation)

    def add_token(self, token):
        self.tokens.append(token)

    def annotations_with_type(self, type_name: str) -> List[Annotation]:
        return self._annotations[type_name]


@dataclass
class Document:
    sentences: List[Sentence]

    @property
    def text(self):
        return "\n".join([s.text for s in self.sentences])

    def sentence_with_idx(self, idx) -> Optional[Sentence]:
        try:
            return self.sentences[idx - 1]
        except IndexError:
            return None

    def add_tokens_as_sentence(self, tokens: List[str]) -> Sentence:
        """
        Builds a Webanno Sentence instance for the token texts, incrementing
        sentence and token indices and calculating (utf-16) offsets for the tokens
        as per the TSV standard. The sentence is added to the document's sentences.

        :param tokens: The tokenized version of param text.
        :return: A Sentence instance.
        """
        text = " ".join(tokens)
        sentence = Sentence(len(self.sentences) + 1, text)

        char_idx = 0
        for token_idx, token_text in enumerate(tokens, start=1):
            token_utf16_length = int(len(token_text.encode('utf-16-le')) / 2)
            end = char_idx + token_utf16_length
            token = Token(sentence=sentence, idx=token_idx, start=char_idx, end=end, text=token_text)
            sentence.add_token(token)
            char_idx = end + 1
        self.sentences.append(sentence)
        return sentence


def _read_token(doc: Document, row: Dict) -> Token:
    """
    Construct a Token from the row object using the sentence from doc.
    This converts the first three columns fo the TSV, e.g.:
        "2-3    13-20    example"
    becomes:
        Token(Sentence(idx=2), idx=3, start=13, end=20, text='example')
    """

    def intsplit(s: str):
        return [int(s) for s in s.split('-')]

    sent_idx, tok_idx = intsplit(row['sent_tok_idx'])
    start, end = intsplit(row['offsets'])
    text = row['token']
    sentence = doc.sentence_with_idx(sent_idx)
    token = Token(sentence, tok_idx, start, end, text)
    sentence.add_token(token)
    return token


def _read_label_and_id(field: str) -> Tuple[str, int]:
    """
    Reads a Webanno TSV field value, returning a label and an id.
    Returns an empty label for placeholder values '_', '*'
    Examples:
        "OBJ[6]" -> ("OBJ", 6)
        "OBJ"    -> ("OBJ", -1)
        "_"      -> ("", None)
        "*[6]"   -> ("", 6)
    """
    match = FIELD_WITH_ID_RE.match(field)
    if match:
        label = match.group(1)
        label_id = int(match.group(2))
    else:
        label = field
        label_id = NO_LABEL_ID

    if FIELD_EMPTY_RE.match(label):
        label = ''

    return label, label_id


def webanno_tsv_read(path) -> Document:
    # TSV files are encoded as utf-8 always as per
    # https://zoidberg.ukp.informatik.tu-darmstadt.de/jenkins/job/WebAnno%20%28GitHub%29%20%28master%29/de.tudarmstadt.ukp.clarin.webanno$webanno-webapp/doclinks/1/#_encoding_and_offsets
    with open(path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()

    comments = [line for line in lines if COMMENT_RE.match(line)]
    data = [line for line in lines if not COMMENT_RE.match(line)]

    matches = [SENTENCE_RE.match(c) for c in comments]
    texts = [m.group(1) for m in matches if m is not None]
    sentences = [Sentence(i + 1, text) for i, text in enumerate(texts)]

    doc = Document(sentences=sentences)

    rows = csv.DictReader(data, dialect=WebannoTsvDialect, fieldnames=TSV_FIELDNAMES)
    for row in rows:

        # The first three columns in each line make up a Token
        token = _read_token(doc, row)
        sentence = token.sentence
        # Each column after the first three is one or more span annotatins
        for span_type in ['lemma', 'pos', 'entity_id', 'named_entity']:
            # There might be multiple annotations in each column field
            if row[span_type] is None:
                logger.warning(f"Empty field '{span_type}' in {path}")
                continue
            values = row[span_type].split('|')
            for value in values:
                label, label_id = _read_label_and_id(value)
                if label != '':
                    a = Annotation(
                        token=token,
                        label=label,
                        span_type=span_type,
                        label_id=label_id,
                    )
                    sentence.add_annotation(a)

    return doc
