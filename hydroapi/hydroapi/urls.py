from django.conf.urls import patterns, include, url
from tastypie.api import Api
from api.resources import MeasurementsResource, AttributesResource

from django.contrib import admin
admin.autodiscover()


v1_api = Api(api_name='v1')
v1_api.register(MeasurementsResource())
v1_api.register(AttributesResource())


urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include(v1_api.urls)),
)
