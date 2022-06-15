# noinspection PyMethodMayBeStatic
from collections import Counter
from typing import Dict, List, Union

import simplejson
from django.core.cache import cache
from django.db.models import QuerySet
from haystack import fields
from haystack.constants import Indexable
from haystack.indexes import SearchIndex

from astrobin.models import Image
from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_images.api.serializers import ImageSerializer
from common.serializers import UserSerializer

PREPARED_FIELD_CACHE_EXPIRATION = 60
PREPARED_IMAGES_CACHE_KEY = 'astrobin_apps_equipment_search_indexed_images_%s_%d'

class EquipmentItemIndex(SearchIndex, Indexable):
    text = fields.CharField(document=True, use_template=True)

    # Top 10 users (by AstroBin Index) who have this item in at least one of their public images.
    equipment_item_users = fields.CharField()

    # Number of users who have used this item.
    equipment_item_user_count = fields.IntegerField()

    # Top 25 images (by likes) that feature this item.
    equipment_item_images = fields.CharField()

    # Number of images that feature this item.
    equipment_item_image_count = fields.IntegerField()

    # This fields is a dictionary of the items that this items is most often used with, and it's only valid for certain
    # combinations:
    #
    # Camera -> Telescope, Filter
    # Telescope -> Camera, Mount
    # Mount -> Telescope
    # Filter -> Camera
    # Accessory -> None
    # Software -> None
    #
    # The dictionary is limited to the top 10 items and is a JSON string  representation of the following object:
    # {
    #   str: number
    # }
    #
    # where:
    #  the key is a a string built with the item's klass and its id, e.g. "CAMERA-1234"
    #  the value is the number of images that this item has in common with it
    equipment_item_most_often_used_with = fields.CharField()

    def image_queryset(self, obj):
        raise NotImplemented

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def _prepare_images_cache(self, obj) -> List[Image]:
        images: List[Image] = cache.get(PREPARED_IMAGES_CACHE_KEY % (obj.__class__.__name__, obj.pk))
        images_and_likes: List[Dict[str, Union[Image, int]]] = []
        if images is None:
            qs: QuerySet = Image.objects.filter(self.image_queryset(obj))
            count: int = qs.count()
            image: Image

            if count > 0:
                for image in qs.iterator():
                    likes: int = image.likes()
                    images_and_likes.append(dict(image=image, likes=likes))

            images_and_likes = sorted(images_and_likes, key=lambda x: x.get('likes'), reverse=True)
            images = [x.get('image') for x in images_and_likes]
            cache.set(
                PREPARED_IMAGES_CACHE_KEY % (obj.__class__.__name__, obj.pk),
                images,
                PREPARED_FIELD_CACHE_EXPIRATION
            )
        return images

    def prepare_equipment_item_users(self, obj) -> List[int]:
        images: List[Image] = self._prepare_images_cache(obj)
        data: str = UserSerializer(list(set([x.user for x in images][:10])), many=True).data
        return simplejson.dumps(data)

    def prepare_equipment_item_user_count(self, obj) -> int:
        images: List[Image] = self._prepare_images_cache(obj)
        count = len(set([x.user for x in images]))
        self.get_model().objects.filter(pk=obj.pk).update(user_count=count)
        return count

    def prepare_equipment_item_images(self, obj) -> List[int]:
        images: List[Image] = self._prepare_images_cache(obj)[:25]
        data: str = ImageSerializer(images, many=True).data
        return simplejson.dumps(data)

    def prepare_equipment_item_image_count(self, obj) -> int:
        images: List[Image] = self._prepare_images_cache(obj)
        count: int = len(images)
        self.get_model().objects.filter(pk=obj.pk).update(image_count=count)
        return count

    def prepare_equipment_item_most_often_used_with(self, obj):
        data: Dict[str, int] = {}
        image: Image
        processing_list = [
            {
                'klass': EquipmentItemKlass.CAMERA,
                'lookup_property': 'imaging_cameras_2',
                'match_properties': ('imaging_telescopes_2', 'filters_2',)
            },
            {
                'klass': EquipmentItemKlass.TELESCOPE,
                'lookup_property': 'imaging_telescopes_2',
                'match_properties': ('imaging_cameras_2', 'mounts_2',)
            },
            {
                'klass': EquipmentItemKlass.MOUNT,
                'lookup_property': 'mounts_2',
                'match_properties': ('imaging_telescopes_2',)
            },
            {
                'klass': EquipmentItemKlass.FILTER,
                'lookup_property': 'filters_2',
                'match_properties': ('imaging_cameras_2',)
            },
        ]

        def _update_data(item: EquipmentItem):
            key: str = f'{item.klass}-{item.id}'
            value: int = data.get(key, 0)
            data[key] = value + 1

        for processing_item in processing_list:
            if processing_item.get('klass') == obj.klass:
                for image in Image.objects.filter(**{processing_item.get('lookup_property'): obj}).iterator():
                    for x in processing_item.get('match_properties'):
                        for item in getattr(image, x).all().iterator():
                            _update_data(item)

        # Only keep those with more than one match.
        data = dict(filter(lambda x: x[1] > 1, data.items()))

        # Limit to 10.
        data = dict(Counter(data).most_common(10))

        return simplejson.dumps(data)

    def get_updated_field(self):
        return 'last_added_or_removed_from_image'
