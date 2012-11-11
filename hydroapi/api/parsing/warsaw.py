# -*- coding: utf-8 -*-

import re
import urllib
import pprint
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup


TRANSLATOR = {
    u'Og\xf3lna liczba mikroorganizm\xf3w': 'Microorganisms overall',
    'Bakterie grupy coli': 'Coli group bacteria',
    'Escherichia coli': 'E. coli bacteria',
    'Clostridium perfringens': 'Clostridium perfringens',
    u'M\u0119tno\u015b\u0107': 'Turbidity',
    'Barwa': 'Color',
    'Zapach': 'Scent',
    u'St\u0119\u017cenie jon\xf3w wodoru\xa0(pH)': 'Hydrogen ion concentration (pH)',
    u'Twardo\u015b\u0107': 'Hardness',
    u'\u017belazo': 'Iron ',
    'Mangan': 'Manganium',
    'Chlorki': 'Chlorides',
    'Amonowy jon': 'Amonium ion',
    'Azotany': 'Nitrate ion',
    'Azotyny': 'Nitrite ion',
    'Chlor wolny': 'Chlorine',
    'Siarczany': 'Sulfates',
    'Fluorki': 'Fluorides',
    'Glin': 'Amelinium ;-)',
    'Kadm': 'Cadmium',
    u'O\u0142\xf3w': 'Lead',
    u'Rt\u0119\u0107': 'Mercury',
    'Nikiel': 'Nickel',
    u'Mied\u017a': 'Copper',
    'Chrom': 'Chromium',
    'Arsen': 'Arsenic',
    'Chloroform': 'Chloroform',
    'Bromodichlorometan': 'Bromodichloromethane',
    'Suma THM': 'THM sum',
}

URLS = [
    'http://www.mpwik.com.pl/dla-klienta/woda/archiwum-jakosci-wody/wodociag-centralny-wrzesien-2012',
    'http://www.mpwik.com.pl/dla-klienta/woda/archiwum-jakosci-wody/wodociag-praski-wrzesien-2012',
    'http://www.mpwik.com.pl/dla-klienta/woda/archiwum-jakosci-wody/wodociag-polnocny-wrzesien-2012'
]

SUBURBS = {
    'http://www.mpwik.com.pl/dla-klienta/woda/archiwum-jakosci-wody/wodociag-centralny-wrzesien-2012': [
        (u'Śródmieście', 'POINT(21.0122287 52.2296756)'),
        (u'Ochota', 'POINT(20.9712206 52.2103359)'),
        (u'Ursus', 'POINT(20.8837885 52.1951226)'),
        (u'Włochy', 'POINT(20.9478161 52.1799062)'),
        (u'Ursynów', 'POINT(21.0291229 52.1378544)'),
    ],
    'http://www.mpwik.com.pl/dla-klienta/woda/archiwum-jakosci-wody/wodociag-praski-wrzesien-2012': [
        (u'Rembertów', 'POINT(21.145839 52.2630714)'),
        (u'Praga południe', 'POINT(21.0840602 52.2416808)'),
        (u'Wawer', 'POINT(21.1782251 52.1962166)'),
        (u'Mokotów', 'POINT(21.0346955 52.194157)'),
        (u'Wilanów', 'POINT(21.1116284 52.1561298)'),
        (u'Falenica', 'POINT(21.2221138 52.1639285)'),
    ],
    'http://www.mpwik.com.pl/dla-klienta/woda/archiwum-jakosci-wody/wodociag-polnocny-wrzesien-2012': [
        (u'Białołęka', 'POINT(21.0076793 52.3289879)'),
        (u'Bielany', 'POINT(20.928664 52.2933234)'),
        (u'Żoliborz', 'POINT(20.9818745 52.2693286)'),
        (u'Targówek', 'POINT(21.0653678 52.2823819)'),
        (u'Wesoła', 'POINT(21.225198 52.2329397)'),
        (u'Pruszków', 'POINT(21.0122287 52.2296756)'),
        (u'Piastów', 'POINT(20.8400429 52.1845184)'),
        (u'Bemowo', 'POINT(20.9113297 52.2409067)'),
    ],
}

UNITS_TRANSLATOR = [
    ('jtk', 'CFU'),
    ('tk', 'CFU'),
]


def convert_entity(ent):
    return BeautifulStoneSoup(ent, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents[0]


def parse():
    data = load_data()
    save(data)


def load_data():
    all_attrs = {}
    for url in URLS:
        raw_html = urllib.urlopen(url).read()
        soup = BeautifulSoup(raw_html, )
        table = soup.find('table').find('table')
        t = []
        for tr in table.findAll('tr'):
            r = []
            for td in tr.findAll('td'):
                r.append(convert_entity(td.text))
            t.append(r)
        row_filter = re.compile(r'\d+\.')
        attrs = {}
        for row in t:
            if row_filter.match(row[0]):
                for k in TRANSLATOR.iterkeys():
                    if row[1].startswith(k):
                        unit = row[2].strip()
                        if unit == '-':
                            unit = ''
                        else:
                            unit = ' ' + unit
                        for pl, eng in UNITS_TRANSLATOR:
                            unit = unit.replace(pl, eng)
                        value = row[3].strip().replace(',', '.')
                        if not value.startswith('-'):
                            attrs[TRANSLATOR[k]] = value + unit
        all_attrs[url] = attrs
    return all_attrs


def save(data):
    from api.models import Measurement, Source, Code, Attribute
    source_name = 'MPWiK'
    source_url = 'http://www.mpwik.com.pl'
    try:
        source = Source.objects.get(name=source_name)
    except Source.DoesNotExist:
        source = Source.objects.create(name=source_name, url=source_url)
    code = Code.objects.get(code=1)
    for url, attrs in data.iteritems():
        for suburb_name, suburb_point in SUBURBS[url]:
            quality = 90 - int(attrs['Microorganisms overall'].split()[0])
            measurement = Measurement.objects.create(location=suburb_point,
                                                     source=source,
                                                     quality=quality,
                                                     code=code,
                                                     location_name=suburb_name)
            for attr_name, attr_value in attrs.iteritems():
                Attribute.objects.create(measurement=measurement,
                                         key=attr_name,
                                         value=attr_value)


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(load_data())
