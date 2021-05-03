import re
from dataclasses import dataclass
from typing import Iterator, Optional, Sequence

from lxml import etree


@dataclass(frozen=True)
class ParsedDate:
    year: str
    month: str = ''
    day: str = ''


@dataclass(frozen=True)
class Unitdate:
    label: str
    text: str
    normal: str


@dataclass(frozen=True)
class Reference:
    normal: str
    text: str
    role: str
    source: str
    auth_file_number: str


@dataclass(frozen=True)
class Person(Reference):
    pass


@dataclass(frozen=True)
class Place(Reference):
    pass


@dataclass(frozen=True)
class Component:
    ead_id: str
    unitid: str
    persons: Sequence[Person]
    places: Sequence[Place]
    unitdate: Optional[Unitdate] = None


def findall(elem: etree.Element, expression: str) -> Sequence[etree.Element]:
    """
    Convenience findall ignoring the element's namespace
    """
    return elem.findall(expression, namespaces={None: etree.QName(elem).namespace})


def localname(element: etree.Element) -> str:
    """
    Convenience localname ignoring the element's namespace
    """
    return etree.QName(element.tag).localname


def parse_unitdate(unitdate: Unitdate) -> (Optional[ParsedDate], Optional[ParsedDate]):
    def parse_single(s: str) -> ParsedDate:
        match = re.match(r'^(\d{4})$', s)
        if match:
            return ParsedDate(year=s)
        match = re.match(r'^(\d{4})-(\d{2})$', s)
        if match:
            return ParsedDate(year=match.group(1), month=match.group(2))
        match = re.match(r'^(\d{4})(\d{2})(\d{2})$', s)
        if match:
            return ParsedDate(year=match.group(1), month=match.group(2), day=match.group(3))
        raise ValueError(f'Cannot parse date:: {s}')

    if unitdate.normal:
        parsed = (parse_single(s) for s in unitdate.normal.split('/'))
        return next(parsed), next(parsed, None)
    else:
        return None, None


def read_unitdate(elem: etree.Element) -> Unitdate:
    return Unitdate(text=elem.text if elem.text else '', label=elem.get('label', ''), normal=elem.get('normal', ''))


def read_reference_attrs(elem: etree.Element) -> {}:
    return dict(text=elem.text if elem.text else '',
                normal=elem.get('normal', ''),
                role=elem.get('role', ''),
                source=elem.get('source', ''),
                auth_file_number=elem.get('authfilenumber', ''))


def read_person(elem: etree.Element) -> Person:
    return Person(**read_reference_attrs(elem))


def read_place(elem: etree.Element) -> Place:
    return Place(**read_reference_attrs(elem))


def read_component(element: etree.Element) -> Component:
    ead_id = element.get('id')
    assert ead_id

    unitid = next(e.text for e in findall(element, 'did/unitid'))
    unitdate = next((read_unitdate(e) for e in findall(element, 'did/unitdate')), None)

    persons = [read_person(elem) for elem in findall(element, 'controlaccess/persname')]
    places = [read_place(elem) for elem in findall(element, 'controlaccess/geogname')]

    return Component(ead_id=ead_id, unitid=unitid, persons=persons, places=places, unitdate=unitdate)


def read_components_from_file(path: str) -> Iterator[Component]:
    for _, element in etree.iterparse(path, events=['end']):
        if localname(element) == 'c':
            yield read_component(element)
            element.clear(keep_tail=True)
