from django.contrib.gis.db import models


class Source(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=255)


class Code(models.Model):
    code = models.IntegerField()
    label = models.CharField(max_length=255)


class Measurement(models.Model):
    location = models.PointField()
    source = models.ForeignKey(Source)
    quality = models.IntegerField()
    comment = models.TextField(blank=True, default='')
    code = models.ForeignKey(Code)
    location_name = models.CharField(max_length=255)

    objects = models.GeoManager()


class Attribute(models.Model):
    measurement = models.ForeignKey(Measurement)
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
