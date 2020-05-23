from django.db import models

from astrobin.models import Image


class ThumbnailGroup(models.Model):
    image = models.ForeignKey(
        Image,
        related_name='thumbnails',
    )

    revision = models.CharField(
        max_length=3,
        default='0',
    )

    real = models.CharField(max_length=512, null=True, blank=True)
    real_inverted = models.CharField(max_length=512, null=True, blank=True)
    hd = models.CharField(max_length=512, null=True, blank=True)
    hd_anonymized = models.CharField(max_length=512, null=True, blank=True)
    hd_inverted = models.CharField(max_length=512, null=True, blank=True)
    hd_sharpened = models.CharField(max_length=512, null=True, blank=True)
    hd_sharpened_inverted = models.CharField(max_length=512, null=True, blank=True)
    regular = models.CharField(max_length=512, null=True, blank=True)
    regular_inverted = models.CharField(max_length=512, null=True, blank=True)
    regular_sharpened = models.CharField(max_length=512, null=True, blank=True)
    regular_sharpened_inverted = models.CharField(max_length=512, null=True, blank=True)
    gallery = models.CharField(max_length=512, null=True, blank=True)
    gallery_inverted = models.CharField(max_length=512, null=True, blank=True)
    collection = models.CharField(max_length=512, null=True, blank=True)
    thumb = models.CharField(max_length=512, null=True, blank=True)
    histogram = models.CharField(max_length=512, null=True, blank=True)
    iotd = models.CharField(max_length=512, null=True, blank=True)
    iotd_candidate = models.CharField(max_length=512, null=True, blank=True)
    story = models.CharField(max_length=512, null=True, blank=True)
    duckduckgo = models.CharField(max_length=512, null=True, blank=True)
    duckduckgo_small = models.CharField(max_length=512, null=True, blank=True)

    def get_all_urls(self):
        # type: () -> list[basestring]

        return [
            self.real,
            self.real_inverted,
            self.hd,
            self.hd_anonymized,
            self.hd_inverted,
            self.regular,
            self.real_inverted,
            self.gallery,
            self.gallery_inverted,
            self.collection,
            self.thumb,
            self.revision,
            self.histogram,
            self.iotd,
            self.iotd_candidate,
            self.story,
            self.duckduckgo,
            self.duckduckgo_small
        ]

    def __unicode__(self):
        return "Thumbnails for image %s" % self.image.title

    class Meta:
        app_label = 'astrobin_apps_images'
        unique_together = ('image', 'revision',)
