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

HEADERS = [
    '#FORMAT=WebAnno TSV 3.1',
    '#T_SP=de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS|PosValue',
    '#T_SP=de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma|value',
    '#T_SP=webanno.custom.LetterEntity|entity_id|value',
    ''
]

TSV_FIELDNAMES = ['sent_tok_idx', 'offsets', 'token', 'pos', 'lemma', 'entity_id', 'named_entity']

# Strings that need to be escaped with a single backslash according to Webanno Appendix B
RESERVED_STRS = ['\\', '[', ']', '|', '_', '->', ';', '\t', '\n', '*']

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

    def __lt__(self, other) -> bool:
        # allow tokens to be sorted if in the same document
        assert self.doc == other.doc
        return self.sentence.idx <= other.sentence.idx and self.idx < other.idx

    @property
    def doc(self) -> 'Document':
        return self.sentence.doc

    def is_at_begin_of_sentence(self) -> bool:
        return self.idx == 1

    def is_at_end_of_sentence(self) -> bool:
        return self.idx == max(t.idx for t in self.sentence.tokens)

    def is_followed_by(self, other: 'Token') -> bool:
        return ((self.sentence == other.sentence and self.idx == other.idx - 1)
                or (self.sentence.is_followed_by(other.sentence)
                    and other.is_at_begin_of_sentence()
                    and self.is_at_end_of_sentence()))


class Annotation:

    def __init__(self, token: Token, span_type: str, label: str, label_id: int = NO_LABEL_ID):
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
    def sentences(self) -> List['Sentence']:
        return list(set(t.sentence for t in self._tokens))

    @property
    def text(self):
        return ' '.join([t.text for t in self._tokens])

    @property
    def tokens(self):
        return list(self._tokens)  # return a read-only copy

    @property
    def doc(self):
        return self._tokens[0].doc

    @property
    def token_texts(self):
        return [token.text for token in self._tokens]

    def merge_other(self, other: 'Annotation'):
        assert (self.span_type == other.span_type)
        assert (self.label == other.label)
        assert (self.label_id == other.label_id)
        assert (self.tokens[-1].is_followed_by(other.tokens[0]))
        self._tokens = sorted(self._tokens + other.tokens)


class Sentence:

    def __init__(self, doc: 'Document', idx: int, text: str):
        self.doc = doc
        self.idx = idx
        self.text = text
        self.tokens: List[Token] = []

    @property
    def token_texts(self) -> List[str]:
        return [token.text for token in self.tokens]

    def add_token(self, token):
        self.tokens.append(token)

    def annotations_with_type(self, type_name: str) -> List[Annotation]:
        return [a for a in self.doc.annotations_with_type(type_name) if self in a.sentences]

    def is_following(self, other: 'Sentence') -> bool:
        return self.doc == other.doc and self.idx == (other.idx + 1)

    def is_followed_by(self, other: 'Sentence') -> bool:
        return other.is_following(self)


class Document:

    def __init__(self, original_path=''):
        self.original_path = original_path
        self.sentences: List[Sentence] = list()
        self._annotations: Dict[str, List[Annotation]] = defaultdict(list)

    def _next_idx(self) -> int:
        return len(self.sentences) + 1

    @property
    def text(self) -> str:
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
        sentence = Sentence(doc=self, idx=self._next_idx(), text=text)

        char_idx = 0
        for token_idx, token_text in enumerate(tokens, start=1):
            token_utf16_length = int(len(token_text.encode('utf-16-le')) / 2)
            end = char_idx + token_utf16_length
            token = Token(sentence=sentence, idx=token_idx, start=char_idx, end=end, text=token_text)
            sentence.add_token(token)
            char_idx = end + 1
        self.add_sentence(sentence)
        return sentence

    def tsv(self) -> str:
        return webanno_tsv_write(self)

    def add_sentence(self, sentence: Sentence):
        sentence.doc = self
        self.sentences.append(sentence)

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
            assert (annotation.doc == self)
            self._annotations[annotation.span_type].append(annotation)

    def annotations_with_type(self, type_name: str) -> List[Annotation]:
        return self._annotations[type_name]


def _unescape(text: str) -> str:
    for s in RESERVED_STRS:
        text = text.replace('\\' + s, s)
    return text


def _escape(text: str) -> str:
    for s in RESERVED_STRS:
        text = text.replace(s, '\\' + s)
    return text


def _read_token(doc: Document, row: Dict) -> Token:
    """
    Construct a Token from the row object using the sentence from doc.
    This converts the first three columns ofo the TSV, e.g.:
        "2-3    13-20    example"
    becomes:
        Token(Sentence(idx=2), idx=3, start=13, end=20, text='example')
    """

    def intsplit(s: str):
        return [int(s) for s in s.split('-')]

    sent_idx, tok_idx = intsplit(row['sent_tok_idx'])
    start, end = intsplit(row['offsets'])
    text = _unescape(row['token'])
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

    return _unescape(label), label_id


def webanno_tsv_read(path) -> Document:
    # TSV files are encoded as utf-8 always as per
    # https://zoidberg.ukp.informatik.tu-darmstadt.de/jenkins/job/WebAnno%20%28GitHub%29%20%28master%29/de.tudarmstadt.ukp.clarin.webanno$webanno-webapp/doclinks/1/#_encoding_and_offsets
    with open(path, mode='r', encoding='utf-8') as f:
        lines = f.readlines()

    comments = [line for line in lines if COMMENT_RE.match(line)]
    data = [line for line in lines if not COMMENT_RE.match(line)]

    matches = [SENTENCE_RE.match(c) for c in comments]
    texts = [m.group(1) for m in matches if m is not None]

    doc = Document(original_path=path)
    for i, text in enumerate(texts):
        sentence = Sentence(doc, idx=i + 1, text=text)
        doc.add_sentence(sentence)

    rows = csv.DictReader(data, dialect=WebannoTsvDialect, fieldnames=TSV_FIELDNAMES)
    for row in rows:

        # The first three columns in each line make up a Token
        token = _read_token(doc, row)
        # Each column after the first three is one or more span annotatins
        for span_type in ['pos', 'lemma', 'entity_id', 'named_entity']:
            if row[span_type] is None:
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
                    doc.add_annotation(a)
    return doc


def _annotations_for_token(token: Token, type_name: str) -> List[Annotation]:
    doc = token.doc
    return [a for a in doc.annotations_with_type(type_name) if token in a.tokens]


def _write_annotation_label(annotation: Annotation) -> str:
    label = _escape(annotation.label)
    if annotation.label_id == NO_LABEL_ID:
        return label
    else:
        return f'{label}[{annotation.label_id}]'


def _write_annotation_layer_fields(token: Token, type_names: List[str]) -> List[str]:
    all_annotations = []
    for type_name in type_names:
        all_annotations += _annotations_for_token(token, type_name)

    # If there are no annotations for this layer '-' is returned for each column
    if not all_annotations:
        return ['_'] * len(type_names)

    all_ids = {a.label_id for a in all_annotations}
    all_ids = all_ids - {NO_LABEL_ID}
    fields = []
    for type_name in type_names:
        annotations = [a for a in all_annotations if a.span_type == type_name]
        labels = []

        # first write annotations without label_ids
        for annotation in [a for a in annotations if a.label_id == NO_LABEL_ID]:
            labels.append(_write_annotation_label(annotation))

        # next we treat id'ed annotations, that need id'ed indicators in columns where no
        # annotation for the id is present
        for lid in sorted(all_ids):
            try:
                annotation = next(a for a in annotations if a.label_id == lid)
                labels.append(_write_annotation_label(annotation))
            except StopIteration:
                labels.append('*' if lid == NO_LABEL_ID else f'*[{lid}]')

        if not labels:
            labels.append('*')

        fields.append('|'.join(labels))

    return fields


def webanno_tsv_write(doc: Document, linebreak='\n') -> str:
    lines = []
    lines += HEADERS

    for sentence in doc.sentences:
        lines.append('')
        lines.append(f'#Text={_escape(sentence.text)}')

        for token in sentence.tokens:
            line = [
                f'{sentence.idx}-{token.idx}',
                f'{token.start}-{token.end}',
                _escape(token.text),
            ]
            line += _write_annotation_layer_fields(token, ['pos'])
            line += _write_annotation_layer_fields(token, ['lemma'])
            line += _write_annotation_layer_fields(token, ['entity_id', 'named_entity'])

            lines.append('\t'.join(line))

    return linebreak.join(lines)
