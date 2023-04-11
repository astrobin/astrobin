# noinspection PyMethodMayBeStatic
import logging

from celery_haystack.indexes import CelerySearchIndex
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import QuerySet
from haystack import fields

from astrobin.models import Image

log = logging.getLogger(__name__)

PREPARED_USER_COUNT_CACHE_KEY = 'equipment_indexes_user_count_%s_%d'
PREPARED_IMAGE_COUNT_CACHE_KEY = 'equipment_indexes_image_count_%s_%d'


class EquipmentBaseIndex(CelerySearchIndex):
    text = fields.CharField(document=True, use_template=True)

    def image_queryset(self, obj):
        raise NotImplemented

    def user_queryset(self, obj):
        raise NotImplemented

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def _prepare_user_count(self, obj) -> int:
        key = PREPARED_USER_COUNT_CACHE_KEY % (obj.__class__.__name__, obj.pk)
        count = cache.get(key)

        if count is not None:
            log.debug(f'{key} found in cache')
            return count

        users: QuerySet = User.objects.filter(self.user_queryset(obj)).distinct()
        count: int = users.count()
        self.get_model().objects.filter(pk=obj.pk).update(user_count=count)

        cache.set(key, count, 60 * 60 * 24)

        return count

    def _prepare_image_count(self, obj) -> int:
        key = PREPARED_IMAGE_COUNT_CACHE_KEY % (obj.__class__.__name__, obj.pk)
        count = cache.get(key)

        if count is not None:
            log.debug(f'{key} found in cache')
            return count

        images: QuerySet = Image.objects.filter(self.image_queryset(obj)).distinct()
        count: int = images.count()
        self.get_model().objects.filter(pk=obj.pk).update(image_count=count)

        cache.set(key, count, 60 * 60 * 24)

        return count

    def get_updated_field(self):
        return 'last_added_or_removed_from_image'
