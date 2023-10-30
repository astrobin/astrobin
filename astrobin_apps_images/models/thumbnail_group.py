from typing import List

from django.db import models

from astrobin.models import Image


class ThumbnailGroup(models.Model):
    image = models.ForeignKey(
        Image,
        related_name='thumbnails',
        on_delete=models.CASCADE
    )

    revision = models.CharField(
        max_length=3,
        default='0',
    )

    real = models.CharField(max_length=512, null=True, blank=True)
    real_anonymized = models.CharField(max_length=512, null=True, blank=True)
    real_inverted = models.CharField(max_length=512, null=True, blank=True)

    qhd = models.CharField(max_length=512, null=True, blank=True)
    qhd_anonymized = models.CharField(max_length=512, null=True, blank=True)
    qhd_inverted = models.CharField(max_length=512, null=True, blank=True)
    qhd_sharpened = models.CharField(max_length=512, null=True, blank=True)
    qhd_sharpened_inverted = models.CharField(max_length=512, null=True, blank=True)
    
    hd = models.CharField(max_length=512, null=True, blank=True)
    hd_anonymized = models.CharField(max_length=512, null=True, blank=True)
    hd_anonymized_crop = models.CharField(max_length=512, null=True, blank=True)
    hd_inverted = models.CharField(max_length=512, null=True, blank=True)
    hd_sharpened = models.CharField(max_length=512, null=True, blank=True)
    hd_sharpened_inverted = models.CharField(max_length=512, null=True, blank=True)
    
    regular = models.CharField(max_length=512, null=True, blank=True)
    regular_anonymized = models.CharField(max_length=512, null=True, blank=True)
    regular_inverted = models.CharField(max_length=512, null=True, blank=True)
    regular_sharpened = models.CharField(max_length=512, null=True, blank=True)
    regular_sharpened_inverted = models.CharField(max_length=512, null=True, blank=True)

    regular_large = models.CharField(max_length=512, null=True, blank=True)
    regular_large_anonymized = models.CharField(max_length=512, null=True, blank=True)
    regular_large_inverted = models.CharField(max_length=512, null=True, blank=True)
    regular_large_sharpened = models.CharField(max_length=512, null=True, blank=True)
    regular_large_sharpened_inverted = models.CharField(max_length=512, null=True, blank=True)
    
    gallery = models.CharField(max_length=512, null=True, blank=True)
    gallery_inverted = models.CharField(max_length=512, null=True, blank=True)
    
    collection = models.CharField(max_length=512, null=True, blank=True)
    
    thumb = models.CharField(max_length=512, null=True, blank=True)
    
    histogram = models.CharField(max_length=512, null=True, blank=True)
    
    iotd = models.CharField(max_length=512, null=True, blank=True)
    iotd_mobile = models.CharField(max_length=512, null=True, blank=True)
    iotd_candidate = models.CharField(max_length=512, null=True, blank=True)
    
    story = models.CharField(max_length=512, null=True, blank=True)
    story_crop = models.CharField(max_length=512, null=True, blank=True)
    
    duckduckgo = models.CharField(max_length=512, null=True, blank=True)
    duckduckgo_small = models.CharField(max_length=512, null=True, blank=True)
    
    instagram_story = models.CharField(max_length=512, null=True, blank=True)

    @staticmethod
    def get_all_sizes() -> List[str]:
        return [
            'real',
            'real_anonymized',
            'real_inverted',
            'hd',
            'hd_anonymized',
            'hd_anonymized_crop',
            'hd_inverted',
            'hd_sharpened',
            'hd_sharpened_inverted',
            'regular',
            'regular_anonymized',
            'regular_inverted',
            'regular_sharpened',
            'regular_sharpened_inverted',
            'regular_large',
            'regular_large_anonymized',
            'regular_large_inverted',
            'regular_large_sharpened',
            'regular_large_sharpened_inverted',
            'gallery',
            'gallery_inverted',
            'collection',
            'thumb',
            'histogram',
            'iotd',
            'iotd_mobile',
            'iotd_candidate',
            'story',
            'story_crop',
            'duckduckgo',
            'duckduckgo_small',
            'instagram_story',
        ]

    def get_all_urls(self) -> List[str]:
        return [getattr(self, x) for x in ThumbnailGroup.get_all_sizes()]

    def __str__(self):
        return "Thumbnails for image %s" % self.image.title

    class Meta:
        app_label = 'astrobin_apps_images'
        unique_together = ('image', 'revision',)
