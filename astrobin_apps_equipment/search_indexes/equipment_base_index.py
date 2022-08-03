# noinspection PyMethodMayBeStatic

from celery_haystack.indexes import CelerySearchIndex
from django.contrib.auth.models import User
from django.db.models import QuerySet
from haystack import fields

from astrobin.models import Image


class EquipmentBaseIndex(CelerySearchIndex):
    text = fields.CharField(document=True, use_template=True)

    def image_queryset(self, obj):
        raise NotImplemented

    def user_queryset(self, obj):
        raise NotImplemented

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def _prepare_user_count(self, obj) -> int:
        users: QuerySet = User.objects.filter(self.user_queryset(obj)).distinct()
        count: int = users.count()
        self.get_model().objects.filter(pk=obj.pk).update(user_count=count)
        return count

    def _prepare_image_count(self, obj) -> int:
        images: QuerySet = Image.objects.filter(self.image_queryset(obj)).distinct()
        count: int = images.count()
        self.get_model().objects.filter(pk=obj.pk).update(image_count=count)
        return count

    def get_updated_field(self):
        return 'last_added_or_removed_from_image'
