import os
import unittest

from data_access.webanno_tsv import webanno_tsv_read, Document, Sentence

READ_INPUT = os.path.join(os.path.dirname(__file__), 'resources', 'test_input.tsv')
TEXT_SENT_1 = "929 Prof. Gerhard Braun an Gerhard Rom , 23 . Juli 1835 Roma li 23 Luglio 1835 ."
TEXT_SENT_2 = "Von den anderen schönen Gefäßen dieser Entdeckungen führen " \
              + "wir hier nur noch einen Kampf des Herkules mit dem Achelous auf ."


class WebannoTsvReadTest(unittest.TestCase):

    def setUp(self) -> None:
        self.doc = webanno_tsv_read(READ_INPUT)

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
        self.assertEqual(TEXT_SENT_1, fst.text)
        self.assertEqual(TEXT_SENT_2, snd.text)

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
            self.assertEquals(start, annotation.start)
            self.assertEqual(end, annotation.end)
            self.assertEquals(label, annotation.label)
            self.assertEquals(label_id, annotation.label_id)
            self.assertEquals(text, annotation.text)