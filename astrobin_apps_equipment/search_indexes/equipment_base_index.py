# noinspection PyMethodMayBeStatic
from typing import Dict, List, Union

import simplejson
from django.core.cache import cache
from django.db.models import QuerySet
from haystack import fields
from celery_haystack.indexes import CelerySearchIndex

from astrobin.models import Image
from astrobin_apps_images.api.serializers import ImageSerializer
from common.serializers import UserSerializer

PREPARED_FIELD_CACHE_EXPIRATION = 60
PREPARED_IMAGES_CACHE_KEY = 'astrobin_apps_equipment_search_indexed_images_%s_%d'


class EquipmentBaseIndex(CelerySearchIndex):
    text = fields.CharField(document=True, use_template=True)

    def image_queryset(self, obj):
        raise NotImplemented

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def _prepare_images_cache(self, obj) -> List[Image]:
        images: List[Image] = cache.get(PREPARED_IMAGES_CACHE_KEY % (obj.__class__.__name__, obj.pk))
        if images is None:
            qs: QuerySet = Image.objects.filter(self.image_queryset(obj)).distinct()
            cache.set(
                PREPARED_IMAGES_CACHE_KEY % (obj.__class__.__name__, obj.pk),
                images,
                PREPARED_FIELD_CACHE_EXPIRATION
            )
        return images

    def _prepare_user_count(self, obj) -> int:
        images: QuerySet = Image.objects.filter(self.image_queryset(obj)).distinct()
        count = len(set([x.user for x in images]))
        self.get_model().objects.filter(pk=obj.pk).update(user_count=count)
        return count

    def _prepare_image_count(self, obj) -> int:
        images: QuerySet = Image.objects.filter(self.image_queryset(obj)).distinct()
        count: int = images.count()
        self.get_model().objects.filter(pk=obj.pk).update(image_count=count)
        return count

    def get_updated_field(self):
        return 'last_added_or_removed_from_image'
