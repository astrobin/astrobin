from django.db import models

from astrobin.models import Image


class KeyValueTag(models.Model):
    image = models.ForeignKey(Image, related_name="keyvaluetags")
    key = models.CharField(max_length=100, null=False, blank=False)
    value = models.CharField(max_length=100, null=False, blank=False)

    def __unicode__(self):
        return u"%s=%s" % (self.key, self.value)

    class Meta:
        app_label = "astrobin_apps_images"
        unique_together = ("image", "key")
