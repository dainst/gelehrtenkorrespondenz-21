import os
import unittest

from data_access.webanno_tsv import webanno_tsv_read, Document, Sentence, Token


def test_file(name):
    return os.path.join(os.path.dirname(__file__), 'resources', name)


class WebannoTsvReadRegularFilesTest(unittest.TestCase):
    TEXT_SENT_1 = "929 Prof. Gerhard Braun an Gerhard Rom , 23 . Juli 1835 Roma li 23 Luglio 1835 ."
    TEXT_SENT_2 = "Von den anderen schönen Gefäßen dieser Entdeckungen führen " \
                  + "wir hier nur noch einen Kampf des Herkules mit dem Achelous auf ."

    def setUp(self) -> None:
        self.doc = webanno_tsv_read(test_file('test_input.tsv'))

    def test_can_read_tsv(self):
        self.assertIsInstance(self.doc, Document)
        self.assertEqual(2, len(self.doc.sentences))

        fst, snd = self.doc.sentences
        self.assertIsInstance(fst, Sentence)
        self.assertIsInstance(snd, Sentence)

    def test_reads_correct_sentences(self):
        fst, snd = self.doc.sentences
        self.assertEqual(1, fst.idx)
        self.assertEqual(2, snd.idx)
        self.assertEqual(self.TEXT_SENT_1, fst.text)
        self.assertEqual(self.TEXT_SENT_2, snd.text)

    def test_reads_correct_document_text(self):
        text = "\n".join((self.TEXT_SENT_1, self.TEXT_SENT_2))
        self.assertEqual(text, self.doc.text)

    def test_reads_correct_tokens(self):
        fst, snd = self.doc.sentences

        spot_checks = [(fst, 4, 18, 23, "Braun"),
                       (fst, 16, 67, 73, "Luglio"),
                       (snd, 1, 81, 84, "Von"),
                       (snd, 14, 164, 169, "Kampf"),
                       (snd, 21, 204, 205, ".")]
        for sentence, idx, start, end, text in spot_checks:
            token = sentence.tokens[idx - 1]
            self.assertEqual(idx, token.idx)
            self.assertEqual(start, token.start)
            self.assertEqual(end, token.end)
            self.assertEqual(text, token.text)

    def test_reads_correct_annotations(self):
        _, snd = self.doc.sentences

        poss = snd.annotations_with_type('pos')
        lemmas = snd.annotations_with_type('lemma')
        entity_ids = snd.annotations_with_type('entity_id')
        named_entities = snd.annotations_with_type('named_entity')

        self.assertEqual(21, len(poss))
        self.assertEqual(22, len(lemmas))
        self.assertEqual(0, len(entity_ids))
        self.assertEqual(3, len(named_entities))

        # some spot checks (first one, last one, some in between
        spot_checks = [(poss[0], 81, 84, 'APPR', -1, 'Von'),
                       (poss[3], 97, 104, 'ADJA', -1, 'schönen'),
                       (poss[11], 153, 157, 'ADV', -1, 'noch'),
                       (poss[20], 204, 205, '$.', -1, '.'),
                       (lemmas[0], 81, 84, 'von', -1, 'Von'),
                       (lemmas[3], 97, 104, 'schön', -1, 'schönen'),
                       (lemmas[12], 153, 157, 'noch', -1, 'noch'),
                       (lemmas[21], 204, 205, '.', -1, '.'),
                       (named_entities[0], 164, 199, 'OBJ', 8, 'Kampf des Herkules mit dem Achelous'),
                       (named_entities[1], 174, 182, 'PERmentioned', 9, 'Herkules'),
                       (named_entities[2], 191, 199, 'PERmentioned', 10, 'Achelous'),
                       ]
        for annotation, start, end, label, label_id, text in spot_checks:
            self.assertEqual(start, annotation.start)
            self.assertEqual(end, annotation.end)
            self.assertEqual(label, annotation.label)
            self.assertEqual(label_id, annotation.label_id)
            self.assertEqual(text, annotation.text)


class WebannoTsvReadFileWithQuotesTest(unittest.TestCase):

    def test_reads_quotes(self):
        self.doc = webanno_tsv_read(test_file('test_input_quotes.tsv'))
        tokens = self.doc.sentences[0].tokens

        self.assertEqual('\"', tokens[3].text)
        self.assertEqual('\"', tokens[5].text)
        self.assertEqual('quotes', tokens[4].text)


class WebannoAddTokensAsSentenceTest(unittest.TestCase):

    def setUp(self) -> None:
        self.doc = Document(sentences=[])

    def test_add_simple(self):
        tokens = ['This', 'is', 'a', 'sentence', '.']
        sentence = self.doc.add_tokens_as_sentence(tokens)

        self.assertIsInstance(sentence, Sentence)
        self.assertEqual(1, sentence.idx)
        self.assertEqual('This is a sentence .', sentence.text)
        self.assertEqual([sentence], self.doc.sentences)

        expected_tokens = [
            Token(sentence, 1, 0, 4, 'This'),
            Token(sentence, 2, 5, 7, 'is'),
            Token(sentence, 3, 8, 9, 'a'),
            Token(sentence, 4, 10, 18, 'sentence'),
            Token(sentence, 5, 19, 20, '.'),
        ]
        self.assertEqual(expected_tokens, sentence.tokens)

    def test_add_unicode_text(self):
        # Example from the WebAnno TSV docs. The smiley should increment
        # the offset by two as it counts for two chars in UTF-16 (as used by Java).
        tokens = ['I', 'like', 'it', '😊', '.']
        sentence = self.doc.add_tokens_as_sentence(tokens)

        self.assertEqual('😊', sentence.tokens[3].text)
        self.assertEqual(10, sentence.tokens[3].start)
        self.assertEqual(12, sentence.tokens[3].end)
        self.assertEqual('.', sentence.tokens[4].text)
        self.assertEqual(13, sentence.tokens[4].start)
