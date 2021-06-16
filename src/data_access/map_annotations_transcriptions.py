from dataclasses import dataclass

from typing import Optional, Sequence


@dataclass(frozen=True)
class Person:
    uid: str  # Either a gnd or kpe id


@dataclass(frozen=True)
class PenPair:
    author: Person
    addressee: Person
    years: Optional[range] = None


@dataclass(frozen=True)
class Transcription:
    zenon_id: str
    pairs: Sequence[PenPair]
    num_letters: int


UNKNONW = Person('unknown-uid')

abeken = Person('116001291')
braun = Person('116415738')
brunn = Person('116777273')
bunsen = Person('118668005')
buensen = UNKNONW
burnouf = Person('117642118')
dressel = Person('116218010')
ferri = Person('1157517366')
friedlaender = Person('116797266')
gatti = Person('1018415580')
gerhard = Person('118717030')
helbig = Person('118710036')
henzen = Person('118710605')
hinck = Person('116896132')
huelsen = Person('117048879')
jahn = Person('118556657')
kekule = Person('118931504')
kellermann = Person('116125888')
koerte = Person('116300892')
lepsius = Person('118727699')
mau = Person('11684244X')
mommsen = Person('118583425')
mommsen_tycho = Person('117125458')
panofka = Person('116023260')
passon = UNKNONW
platner = Person('103086609')
purgold = Person('116313374')
ritschl = Person('118745441')
ronconi = UNKNONW
schlie = Person('11732762X')
studniczka = Person('117354325')
stuerenburg = Person('325898')
welcker = Person('118630741')

transcriptions = [
    Transcription('000880098', [PenPair(braun, gerhard, range(1832, 1835 + 1))], 75),
    Transcription('000882126', [PenPair(braun, gerhard, range(1835, 1837 + 1))], 69),
    Transcription('000882135', [PenPair(braun, gerhard, range(1838, 1840 + 1))], 97),
    Transcription('000882420', [PenPair(braun, gerhard, range(1841, 1843 + 1))], 87),
    Transcription('000882421', [PenPair(braun, gerhard, range(1844, 1848 + 1))], 117),
    Transcription('000882422', [PenPair(braun, gerhard, range(1849, 1856 + 1))], 111),
    Transcription('000882425', [PenPair(braun, henzen, range(1843, 1855 + 1)),
                                PenPair(braun, abeken),
                                PenPair(braun, lepsius),
                                PenPair(braun, purgold),
                                PenPair(braun, jahn),
                                PenPair(braun, brunn)], 107),
    Transcription('000883445', [PenPair(brunn, braun, range(1842, 1844 + 1)),
                                PenPair(brunn, helbig, range(1863, 1886 + 1)),
                                PenPair(brunn, jahn, range(1861, 1864 + 1))], 49),
    Transcription('000883968', [PenPair(brunn, gerhard, range(1847, 1866 + 1))], 46),
    Transcription('000883974', [PenPair(brunn, gerhard, range(1861, 1867 + 1))], 37),
    Transcription('000883983', [PenPair(brunn, henzen, range(1844, 1857 + 1))], 81),
    Transcription('000884002', [PenPair(brunn, henzen, range(1858, 1864 + 1))], 88),
    Transcription('000884007', [PenPair(brunn, henzen, range(1865, 1885 + 1))], 87),
    Transcription('000884346', [PenPair(bunsen, braun),
                                PenPair(bunsen, brunn),
                                PenPair(bunsen, henzen),
                                PenPair(bunsen, kellermann),
                                PenPair(bunsen, lepsius),
                                PenPair(bunsen, panofka)], 161),
    Transcription('000884347', [PenPair(friedlaender, henzen, range(1845, 1883 + 1))], 92),
    Transcription('000884476', [PenPair(gerhard, braun, range(1833, 1835 + 1))], 74),
    Transcription('000884487', [PenPair(gerhard, braun, range(1836, 1837 + 1))], 95),
    Transcription('000884500', [PenPair(gerhard, braun, range(1838, 1839 + 1))], 59),
    Transcription('000884505', [PenPair(gerhard, braun, range(1840, 1841 + 1))], 67),
    Transcription('000884507', [PenPair(gerhard, braun, range(1842, 1843 + 1))], 66),
    Transcription('000884517', [PenPair(gerhard, braun, range(1844, 1856 + 1))], 99),
    Transcription('001313531', [PenPair(gerhard, brunn, range(1846, 1867 + 1))], 112),
    Transcription('001313708', [PenPair(gerhard, bunsen, range(1829, 1837 + 1))], 46),
    Transcription('001313719', [PenPair(gerhard, henzen, range(1843, 1850 + 1))], 101),
    Transcription('001313722', [PenPair(gerhard, henzen, range(1851, 1856 + 1))], 119),
    Transcription('001313735', [PenPair(gerhard, henzen, range(1857, 1859 + 1))], 111),
    Transcription('001313737', [PenPair(gerhard, henzen, range(1860, 1862 + 1))], 100),
    Transcription('001313747', [PenPair(gerhard, henzen, range(1863, 1865 + 1))], 108),
    Transcription('001313748', [PenPair(gerhard, henzen, range(1866, 1867 + 1)),
                                PenPair(gerhard, helbig),
                                PenPair(gerhard, lepsius)], 99),
    Transcription('001313751', [PenPair(helbig, brunn, range(1863, 1889 + 1))], 116),
    Transcription('001313968', [PenPair(helbig, gerhard, range(1862, 1867 + 1))], 61),
    Transcription('001313974', [PenPair(helbig, henzen, range(1863, 1875 + 1))], 119),
    Transcription('001313981', [PenPair(helbig, henzen, range(1876, 1886 + 1))], 63),
    Transcription('001314006', [PenPair(helbig, dressel),
                                PenPair(helbig, gatti),
                                PenPair(helbig, koerte),
                                PenPair(helbig, lepsius),
                                PenPair(helbig, mau),
                                PenPair(helbig, ritschl),
                                PenPair(helbig, ronconi),
                                PenPair(helbig, studniczka, range(1873, 1899 + 1))], 86),
    Transcription('001314816', [PenPair(henzen, helbig, range(1865, 1886 + 1))], 126),
    Transcription('001314234', [PenPair(henzen, braun, range(1843, 1846 + 1))], 30),
    Transcription('001314238', [PenPair(henzen, brunn, range(1844, 1856 + 1))], 99),
    Transcription('001314308', [PenPair(henzen, brunn, range(1857, 1865 + 1))], 123),
    Transcription('001314312', [PenPair(henzen, brunn, range(1866, 1886 + 1))], 104),
    Transcription('001314322', [PenPair(henzen, gerhard, range(1843, 1850 + 1))], 113),
    Transcription('001314449', [PenPair(henzen, gerhard, range(1851, 1855 + 1))], 101),
    Transcription('001314465', [PenPair(henzen, gerhard, range(1856, 1857 + 1))], 77),
    Transcription('001314480', [PenPair(henzen, gerhard, range(1858, 1859 + 1))], 91),
    Transcription('001314520', [PenPair(henzen, gerhard, range(1860, 1861 + 1))], 88),
    Transcription('001314523', [PenPair(henzen, gerhard, range(1862, 1864 + 1))], 96),
    Transcription('001314525', [PenPair(henzen, gerhard, range(1865, 1867 + 1))], 112),
    Transcription('001314529', [PenPair(henzen, buensen),
                                PenPair(henzen, burnouf),
                                PenPair(henzen, hinck),
                                PenPair(henzen, jahn),
                                PenPair(henzen, kekule),
                                PenPair(henzen, lepsius),
                                PenPair(henzen, mau),
                                PenPair(henzen, passon),
                                PenPair(henzen, platner),
                                PenPair(henzen, schlie),
                                PenPair(henzen, stuerenburg)], 132),
    Transcription('001314932', [PenPair(huelsen, henzen),
                                PenPair(huelsen, ferri)], 103),
    Transcription('001314934', [PenPair(jahn, henzen),
                                PenPair(jahn, braun),
                                PenPair(jahn, brunn),
                                PenPair(jahn, gerhard),
                                PenPair(jahn, helbig),
                                PenPair(jahn, abeken)], 91),
    Transcription('001315088', [PenPair(lepsius, henzen, range(1858, 1871 + 1)),
                                PenPair(lepsius, helbig, range(1858, 1871 + 1))], 118),
    Transcription('001315090', [PenPair(lepsius, henzen, range(1872, 1884 + 1)),
                                PenPair(lepsius, helbig, range(1872, 1884 + 1))], 175),
    Transcription('001315095', [PenPair(mommsen, brunn, range(1845, 1893 + 1))], 103),
    Transcription('001315097', [PenPair(mommsen, helbig, range(1872, 1886 + 1))], 28),
    Transcription('001315098', [PenPair(mommsen, henzen, range(1844, 1848 + 1))], 52),
    Transcription('001315129', [PenPair(mommsen, henzen, range(1849, 1853 + 1))], 53),
    Transcription('001315132', [PenPair(mommsen, henzen, range(1854, 1860 + 1))], 71),
    Transcription('001315133', [PenPair(mommsen, jahn, range(1845, 1845 + 1)),
                                PenPair(mommsen, henzen, range(1861, 1886 + 1))], 163),
    Transcription('001315140', [PenPair(mommsen_tycho, henzen)], 22),
    Transcription('001315141', [PenPair(ritschl, braun, range(1833, 1849 + 1)),
                                PenPair(ritschl, helbig, range(1868, 1870 + 1)),
                                PenPair(ritschl, gerhard, range(1833, 1833 + 1))], 31),
    Transcription('001315200', [PenPair(ritschl, henzen, range(1846, 1856 + 1))], 47),
    Transcription('001315201', [PenPair(ritschl, henzen, range(1857, 1876 + 1))], 72),
    Transcription('001315202', [PenPair(welcker, gerhard, range(1828, 1856 + 1)),
                                PenPair(welcker, braun, range(1837, 1849 + 1))], 67),
    Transcription('001315203', [PenPair(welcker, henzen, range(1843, 1864 + 1))], 73),
    Transcription('001315204', [PenPair(welcker, jahn, range(1841, 1854 + 1))], 35),
]


def pair_fits(pair: PenPair, author_id: str, adressee_id: str, year: Optional[int] = None) -> bool:
    if pair.author.uid == author_id and pair.addressee.uid == adressee_id:
        if not pair.years:
            return True
        else:
            # If param year is not given but the pair has a years range, we cannot
            # decide if the pair fits. Thus we return False.
            return year in pair.years
    return False


def find_transcription(author_id: str, adressee_id: str, year: Optional[int] = None) -> Optional[Transcription]:
    return next((t for t in transcriptions for p in t.pairs if pair_fits(p, author_id, adressee_id, year)), None)


def find_transcription_zenon_id(author_id: str, adressee_id: str, year: Optional[int] = None) -> str:
    transcription = find_transcription(author_id, adressee_id, year)
    return transcription.zenon_id if transcription else ''
