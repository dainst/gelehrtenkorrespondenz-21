import unittest
from xml.etree import ElementTree

from src.data_access.ead_xml import (
    parse_unitdate,
    parse_addressee_place,
    read_components_from_file,
    read_note,
    read_person,
    read_place,
    read_unitdate,
    Note,
    Person,
    Place,
    Unitdate,
    ParsedDate
)
from .test_util import test_file


def wrap_xml(xml: str) -> ElementTree.Element:
    return ElementTree.fromstring(xml)


class EadXmlReadTest(unittest.TestCase):

    def test_reads_component_data(self):
        components = list(read_components_from_file(test_file('test_input_ead.xml')))
        self.assertEqual(2, len(components))

        fst, snd = components
        self.assertEqual('DE-611-HS-3342702', fst.ead_id)
        self.assertEqual('DE-611-HS-3342708', snd.ead_id)
        self.assertEqual('D-DAI-Z-AdZ-NL-WitK-GerE-WitK-001', fst.unitid)
        self.assertEqual('D-DAI-Z-AdZ-NL-WitK-GerE-WitK-002', snd.unitid)

        self.assertEqual(2, len(fst.persons))
        self.assertEqual(2, len(snd.persons))
        self.assertTrue(all(type(e) == Person for e in fst.persons + snd.persons))

        self.assertEqual(1, len(fst.places))
        self.assertEqual(1, len(snd.places))
        self.assertTrue(all(type(e) == Place for e in fst.places + snd.places))

        self.assertIsInstance(fst.unitdate, Unitdate)
        self.assertIsInstance(snd.unitdate, Unitdate)

        self.assertIsInstance(fst.note, Note)
        self.assertIsNone(snd.note)

    def test_reads_person_or_place(self):
        xml = '<element role="ROLE" normal="NAME" source="GND" authfilenumber="123456">CONTENT</element>'
        attrs = dict(normal='NAME', text='CONTENT', role='ROLE', source='GND', auth_file_number='123456')
        self.assertEqual(Person(**attrs), read_person(wrap_xml(xml)))
        self.assertEqual(Place(**attrs), read_place(wrap_xml(xml)))

    def test_reads_person_or_place_with_incomplete_fields(self):
        xml = '<element role="ROLE" normal="NAME"></element>'
        attrs = dict(normal='NAME', text='', role='ROLE', source='', auth_file_number='')
        self.assertEqual(Person(**attrs), read_person(wrap_xml(xml)))
        self.assertEqual(Place(**attrs), read_place(wrap_xml(xml)))
        self.assertEqual(Person('', '', '', '', ''), read_person(wrap_xml('<element />')))

    def test_reads_unitdate(self):
        xml = '<unitdate label="Entstehungsdatum" normal="18220913">13.09.1822</unitdate>'
        date = Unitdate(label='Entstehungsdatum', normal='18220913', text='13.09.1822')
        self.assertEqual(date, read_unitdate(wrap_xml(xml)))
        self.assertEqual(Unitdate('', '', ''), read_unitdate(wrap_xml('<unitdate></unitdate>')))

    def test_reads_note(self):
        xml = '<note label="Bemerkung" audience="external"><p>Empfängerort: Breslau</p></note>'
        note = Note(label='Bemerkung', audience='external', text='Empfängerort: Breslau')
        self.assertEqual(note, read_note(wrap_xml(xml)))
        self.assertEqual(Note('', '', ''), read_note(wrap_xml('<note />')))


class ParseUnitDateTest(unittest.TestCase):

    def test_parse_expected_formats(self):
        inputs_outputs = [
            # A single start value
            ('19990101', (ParsedDate(year='1999', month='01', day='01'), None)),
            ('1999-01', (ParsedDate(year='1999', month='01'), None)),
            ('1999', (ParsedDate(year='1999'), None)),
            # start and end values
            ('19990101/20001212', (ParsedDate('1999', '01', '01'), ParsedDate('2000', '12', '12'))),
            ('1999-01/1999-02', (ParsedDate('1999', '01'), ParsedDate('1999', '02'))),
            ('1999/2000', (ParsedDate('1999'), ParsedDate('2000'))),
            # Mixed formats for start/end are parsed
            ('20001212/2001-02', (ParsedDate('2000', '12', '12'), ParsedDate('2001', '02'))),
            ('20001212/2001', (ParsedDate('2000', '12', '12'), ParsedDate('2001'))),
            ('1999-01/20001212', (ParsedDate('1999', '01'), ParsedDate('2000', '12', '12'))),
            ('1999-01/2000', (ParsedDate('1999', '01'), ParsedDate('2000'))),
            ('1999/20001231', (ParsedDate('1999'), ParsedDate('2000', '12', '31'))),
            ('1999/2000-03', (ParsedDate('1999'), ParsedDate('2000', '03'))),
            # Does not validate the input
            ('12345678', (ParsedDate(year='1234', month='56', day='78'), None)),
            # Returns empty on empty input
            ('', (None, None)),
            (None, (None, None))
        ]
        for val, expected in inputs_outputs:
            self.assertEqual(expected, parse_unitdate(Unitdate('', '', val)))

    def test_throws_on_unexpected_formats(self):
        inputs = ['abc', '2012-04-04', '123456789', '123', '1999-1-02', '1999-01-2', '199-01-01']
        for val in inputs:
            with self.assertRaises(ValueError):
                parse_unitdate(Unitdate('', '', val))


class ParsePlaceFromNoteTest(unittest.TestCase):

    def test_parse_expected_formats(self):
        inputs_outputs = [
            ('Empfängerort: ABC', ('ABC', '', '')),
            ('Empfangerort: ABC', ('ABC', '', '')),
            ('Empfangerort ABC', ('ABC', '', '')),
            ('Empfangerort: \t   ABC', ('ABC', '', '')),
            ('Empfängerort: ABC (GND: 1234-5)', ('ABC', 'GND', '1234-5')),
            ('Empfangerort: ABC (GND: 1234-5)', ('ABC', 'GND', '1234-5')),
            ('Empfängerort ABC (GND: 1234-5)', ('ABC', 'GND', '1234-5')),
            ('Empfängerort: \t   ABC   (GND:    1234-5)', ('ABC', 'GND', '1234-5')),
            ('Empfängerort: ABC D\'EF-GH', ('ABC D\'EF-GH', '', '')),
            ('Empfängerort: ABC D\'EF-GH (GND: 1234-5)', ('ABC D\'EF-GH', 'GND', '1234-5')),
        ]
        for val, (normal, source, auth_file_number) in inputs_outputs:
            expected = Place(normal=normal, source=source, auth_file_number=auth_file_number,
                             text=val, role='Empfängerort')
            self.assertEqual(expected, parse_addressee_place(val))
            self.assertEqual(expected, parse_addressee_place('line-before\n' + val + '\nline-after'))
            self.assertEqual(expected, parse_addressee_place('text-before  ' + val + '\nline-after'))

    def test_parse_empty_or_unexpected(self):
        inputs = ['', 'abcd', 'Empfängerort: ']
        for val in inputs:
            self.assertIsNone(parse_addressee_place(val))
