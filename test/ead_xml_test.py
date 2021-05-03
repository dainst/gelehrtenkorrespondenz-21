import unittest
from xml.etree import ElementTree

from src.data_access.ead_xml import (
    read_components_from_file,
    read_person,
    read_place,
    read_unitdate,
    Person,
    Place,
    Unitdate
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
