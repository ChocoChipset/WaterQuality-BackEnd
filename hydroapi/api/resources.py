import re
import json
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer
from api.models import Measurement


class CamelCaseJSONSerializer(Serializer):
    formats = ['json']
    content_types = {
        'json': 'application/json',
    }

    def to_json(self, data, options=None):
        # Changes underscore_separated names to camelCase names to go from python convention to javacsript convention
        data = self.to_simple(data, options)

        def underscoreToCamel(match):
            return match.group()[0] + match.group()[2].upper()

        def camelize(data):
            if isinstance(data, dict):
                new_dict = {}
                for key, value in data.items():
                    new_key = re.sub(r"[a-z]_[a-z]", underscoreToCamel, key)
                    new_dict[new_key] = camelize(value)
                return new_dict
            if isinstance(data, (list, tuple)):
                for i in range(len(data)):
                    data[i] = camelize(data[i])
                return data
            return data

        camelized_data = camelize(data)

        return json.dumps(camelized_data, sort_keys=True)

    def from_json(self, content):
        # Changes camelCase names to underscore_separated names to go from javascript convention to python convention
        data = json.loads(content)

        def camelToUnderscore(match):
            return match.group()[0] + "_" + match.group()[1].lower()

        def underscorize(data):
            if isinstance(data, dict):
                new_dict = {}
                for key, value in data.items():
                    new_key = re.sub(r"[a-z][A-Z]", camelToUnderscore, key)
                    new_dict[new_key] = underscorize(value)
                return new_dict
            if isinstance(data, (list, tuple)):
                for i in range(len(data)):
                    data[i] = underscorize(data[i])
                return data
            return data

        underscored_data = underscorize(data)
        return underscored_data


class MeasurementsResource(ModelResource):
    pk = fields.IntegerField(attribute='id')
    latitude = fields.FloatField(attribute='location__y')
    longitude = fields.FloatField(attribute='location__x')
    source_name = fields.CharField(attribute='source__name')
    source_url = fields.CharField(attribute='source__url')
    code = fields.IntegerField(attribute='code__code')

    class Meta:
        queryset = Measurement.objects.all()
        default_format = 'application/json'
        excludes = ['id', 'location']
        serializer = CamelCaseJSONSerializer()
        include_resource_uri = False

    def determine_format(self, request):
        return self._meta.default_format
