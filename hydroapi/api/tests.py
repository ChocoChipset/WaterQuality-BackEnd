import json
from django.test import TestCase
from django.test.client import Client
from django.contrib.gis.geos import Point
from api.models import Measurement, Code, Source


class MeasurementsResourceTest(TestCase):
    MEASUREMENT = {'pk': 1,
                   'latitude': 53,
                   'longitude': 20.937388,
                   'sourceName': 'Dummy source',
                   'sourceUrl': 'http://example.com',
                   'quality': 87,
                   'comment': '',
                   'code': 1,
                   'locationName': 'Warsaw'}
    ATTRIBUTES = {
        'attr1': '1',
        'attr2': '4',
        'attr3': '3.14',
        'attr4': '6',
        'attr5': 'dummy text value',
    }

    def setUp(self):
        self.client = Client()
        code = Code.objects.get(code=1)
        source_url = self.MEASUREMENT['sourceUrl']
        source = Source.objects.get(url=source_url)
        location = Point(
            self.MEASUREMENT['longitude'], self.MEASUREMENT['latitude'])
        location_name = self.MEASUREMENT['locationName']
        measurement = Measurement.objects.create(pk=self.MEASUREMENT['pk'],
                                                 location=location,
                                                 source=source,
                                                 quality=87,
                                                 code=code,
                                                 location_name=location_name)
        self.measurement = measurement

    def assert_dict_equal(self, a, b):
        self.assertEqual(len(a), len(b))
        for k in a.iterkeys():
            self.assertEqual(a[k], b[k], k)

    def test_json_is_default(self):
        response = self.client.get('/v1/measurements/')
        try:
            json.loads(response.content)
        except ValueError:
            self.fail('Response isn\'t a valid json')

    def test_collection_retrieval(self):
        response = self.client.get('/v1/measurements/')
        elements = json.loads(response.content)
        self.assert_dict_equal(elements['objects'][0], self.MEASUREMENT)

    def test_single_measurement_retrieval(self):
        response = self.client.get('/v1/measurements/1/')
        obj = json.loads(response.content)
        self.assert_dict_equal(obj, self.MEASUREMENT)

   #def test_attribute_retrieval(self):
   #    response = self.client.get('/v1/measurements/1/attributes/')
   #    attributes = json.loads(response.content)
   #    self.assert_dict_equal(attributes, self.ATTRIBUTES)


class RetrievalByLocationTest(TestCase):
    MEASUREMENTS = [
        {'pk': 1,
         'latitude': 40.714623,
         'longitude': -74.006605,
         'source': 1,
         'quality': 87,
         'comment': '',
         'code': 1,
         'locationName': 'New York'},
        {'pk': 2,
         'latitude': 53,
         'longitude': 20.937388,
         'source': 1,
         'quality': 87,
         'comment': '',
         'code': 1,
         'locationName': 'Warsaw'}
    ]

    def setUp(self):
        self.client = Client()
        for m in self.MEASUREMENTS:
            code = Code.objects.get(code=m['code'])
            source = Source.objects.get(pk=m['source'])
            location = Point(m['longitude'], m['latitude'])
            location_name = m['locationName']
            Measurement.objects.create(pk=m['pk'],
                                       location=location,
                                       source=source,
                                       quality=87,
                                       code=code,
                                       location_name=location_name)

    def test_range(self):
        location = (20, 170)
        response = self.client.get('/v1/measurements/%lf/%lf/' % location)
        elements = json.loads(response.content)
        self.assertEqual(len(elements['objects']), 2)

    def test_sorting_by_distance_from_point(self):
        location = (50, 20)
        response = self.client.get('/v1/measurements/%lf/%lf/' % location)
        elements = json.loads(response.content)
        self.assertEqual(len(elements['objects']), 2)
        for i, name in enumerate(['Warsaw', 'New York']):
            self.assertEqual(elements['objects'][i]['locationName'], name)

    def test_sorting_by_distance_from_point_with_distance(self):
        location = (53, 21)
        response = self.client.get('/v1/measurements/%lf/%lf/1000000/' % location)
        elements = json.loads(response.content)
        self.assertEqual(len(elements['objects']), 1)
        for i, name in enumerate(['Warsaw']):
            self.assertEqual(elements['objects'][i]['locationName'], name)
