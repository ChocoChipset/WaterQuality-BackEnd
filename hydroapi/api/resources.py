import re
import json
from django.conf.urls import url
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from tastypie import fields
from tastypie.utils import trailing_slash
from tastypie.resources import ModelResource, ALL
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
        filtering = {
            'lat': ALL,
            'long': ALL,
            'distance': ALL,
            'dlat': ALL,
            'dlong': ALL,
        }

    def prepend_urls(self):
        return [
            url(r'^(?P<resource_name>%s)/(?P<lat>-?\d+(\.\d+)?)/(?P<long>-?\d+(\.\d+)?)(/(?P<distance>\d+))?%s$' % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_list'), name='api_get_for_coord'),
            url(r'^(?P<resource_name>%s)/(?P<lat>-?\d+(\.\d+)?)/(?P<long>-?\d+(\.\d+)?)/(?P<dlat>\d+(\.\d+)?)/(?P<dlong>\d+(\.\d+)?)%s$' % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_list'), name='api_get_for_coord_bb'),
        ]

    def get_list(self, request, **kwargs):
        objects = self.obj_get_list(request=request, **self.remove_api_resource_names(kwargs))
        sorted_objects = self.apply_sorting(objects, options=request.GET, **kwargs)
        paginator = self._meta.paginator_class(request.GET, sorted_objects, resource_uri=self.get_resource_uri(), limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name)
        to_be_serialized = paginator.page()
        bundles = [self.build_bundle(obj=obj, request=request) for obj in to_be_serialized[self._meta.collection_name]]
        to_be_serialized[self._meta.collection_name] = [self.full_dehydrate(bundle) for bundle in bundles]
        to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
        return self.create_response(request, to_be_serialized)

    def build_filters(self, filters=None):
        # Here be dragons
        filters_to_bypass = ['lat', 'long', 'distance', 'dlat', 'dlong']
        bypass = {}
        if filters is not None:
            for filter_name in filters_to_bypass:
                if filter_name in filters:
                    bypass[filter_name] = filters.pop(filter_name)[0]
        filters = super(MeasurementsResource, self).build_filters(filters=filters)
        filters.update(bypass)
        return filters

    def apply_filters(self, request, applicable_filters):
        point = None
        distance = None
        dlat, dlong = None, None
        if 'lat' in applicable_filters and 'long' in applicable_filters:
            latitude = float(applicable_filters.pop('lat'))
            longitude = float(applicable_filters.pop('long'))
            point = Point(longitude, latitude)
            if 'distance' in applicable_filters:
                distance = applicable_filters.pop('distance')
            elif 'dlat' in applicable_filters and 'dlong' in applicable_filters:
                dlat = float(applicable_filters.pop('dlat'))
                dlong = float(applicable_filters.pop('dlong'))
        filtered = super(MeasurementsResource, self).apply_filters(request, applicable_filters)
        if point is not None:
            if distance is not None:
                filtered = filtered.filter(location__distance_lte=(point, D(m=int(distance))))
            elif dlat is not None and dlong is not None:
                bbox = [point.x - dlong, point.y - dlat, point.x + dlong, point.y + dlat]
                geom = Polygon.from_bbox(bbox)
                filtered = filtered.filter(location__coveredby=geom)
        return filtered

    def apply_sorting(self, obj_list, options=None, **kwargs):
        if 'lat' in kwargs and 'long' in kwargs:
            point = Point(float(kwargs['long']), float(kwargs['lat']))
            obj_list = obj_list.distance(point).order_by('distance')
        return obj_list

    def determine_format(self, request):
        return self._meta.default_format
