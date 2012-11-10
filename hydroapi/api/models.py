from django.contrib.gis.db import models


class Source(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=255)

    def __unicode__(self):
        return u'Source(%s, %s)' % (self.name, self.url)


class Code(models.Model):
    code = models.IntegerField()
    label = models.CharField(max_length=255)

    def __unicode__(self):
        return u'Code(%d, %s)' % (self.code, self.label)


class Measurement(models.Model):
    location = models.PointField()
    source = models.ForeignKey(Source)
    quality = models.IntegerField()
    comment = models.TextField(blank=True, default='')
    code = models.ForeignKey(Code)
    location_name = models.CharField(max_length=255)

    objects = models.GeoManager()

    def __unicode__(self):
        return u'Measurement(%s, %d, %lf, %lf)' % (self.location_name,
                                                   self.quality,
                                                   self.location.y,
                                                   self.location.x)


class Attribute(models.Model):
    measurement = models.ForeignKey(Measurement)
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __unicode__(self):
        return u'Attribute(%d, %s=%s)' % (self.measurement.id,
                                          self.key,
                                          self.value)
