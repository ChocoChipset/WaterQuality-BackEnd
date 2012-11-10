from django.contrib import admin
from api.models import Measurement, Code, Source, Attribute

for model in [Measurement, Code, Source, Attribute]:
    admin.site.register(model)
