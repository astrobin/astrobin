# noinspection PyMethodMayBeStatic
import logging
from collections import Counter
from typing import Dict

import simplejson
from django.core.cache import cache
from haystack import fields

from astrobin.models import Image
from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.search_indexes.equipment_base_index import EquipmentBaseIndex

log = logging.getLogger('apps')

PREPARED_MOST_OFTEN_USED_WITH_CACHE_KEY = 'equipment_indexes_most_often_used_with_%s_%d'


class EquipmentItemIndex(EquipmentBaseIndex):
    # Number of users who have used this item.
    equipment_item_user_count = fields.IntegerField()

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

    def prepare_equipment_item_user_count(self, obj) -> int:
        return self._prepare_user_count(obj)

    def prepare_equipment_item_image_count(self, obj) -> int:
        return self._prepare_image_count(obj)

    def prepare_equipment_item_most_often_used_with(self, obj):
        key = PREPARED_MOST_OFTEN_USED_WITH_CACHE_KEY % (obj.__class__.__name__, obj.pk)
        data = cache.get(key)

        if data:
            log.debug(f'{key} found in cache')
            return data

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
        data = simplejson.dumps(dict(Counter(data).most_common(10)))

        cache.set(key, data, 60 * 60 * 24)

        return data
