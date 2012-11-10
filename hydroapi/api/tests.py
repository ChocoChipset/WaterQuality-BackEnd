"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import json
from django.test import TestCase
from django.test.client import Client
from django.contrib.gis.geos import Point
from api.models import Measurement, Code, Source


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


class MeasurementsResourceTest(TestCase):
    MEASUREMENT = {
        'pk': 1,
        'latitude': 52.202683,
        'longitude': 20.937388,
        'sourceName': 'Dummy source',
        'sourceUrl': 'http://example.com',
        'quality': 87,
        'comment': '',
        'code': 1,
        'locationName': 'Warsaw',
    }

    def setUp(self):
        self.client = Client()
        code = Code.objects.create(code=1, label='OK')
        source_name = self.MEASUREMENT['sourceName']
        source_url = self.MEASUREMENT['sourceUrl']
        source = Source.objects.create(name=source_name, url=source_url)
        location = Point(self.MEASUREMENT['longitude'], self.MEASUREMENT['latitude'])
        location_name = self.MEASUREMENT['locationName']
        measurement = Measurement.objects.create(location=location,
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
