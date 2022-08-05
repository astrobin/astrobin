# noinspection PyMethodMayBeStatic

from django.db.models import Q
from haystack import fields
from haystack.constants import Indexable

from astrobin_apps_equipment.models import EquipmentBrand
from astrobin_apps_equipment.search_indexes.equipment_base_index import EquipmentBaseIndex


class EquipmentBrandIndex(EquipmentBaseIndex, Indexable):
    # Number of users who have used this brand.
    equipment_brand_user_count = fields.IntegerField()

    # Number of images that feature this brand.
    equipment_brand_image_count = fields.IntegerField()

    def get_model(self):
        return EquipmentBrand

    def image_queryset(self, obj: EquipmentBrand) -> Q:
        return \
            Q(imaging_telescopes_2__brand=obj) | \
            Q(imaging_cameras_2__brand=obj) | \
            Q(mounts_2__brand=obj) | \
            Q(filters_2__brand=obj) | \
            Q(accessories_2__brand=obj) | \
            Q(software_2__brand=obj) | \
            Q(guiding_telescopes_2__brand=obj) | \
            Q(guiding_cameras_2__brand=obj)

    def user_queryset(self, obj: EquipmentBrand) -> Q:
        return \
            Q(image__imaging_telescopes_2__brand=obj) | \
            Q(image__imaging_cameras_2__brand=obj) | \
            Q(image__mounts_2__brand=obj) | \
            Q(image__filters_2__brand=obj) | \
            Q(image__accessories_2__brand=obj) | \
            Q(image__software_2__brand=obj) | \
            Q(image__guiding_telescopes_2__brand=obj) | \
            Q(image__guiding_cameras_2__brand=obj)

    def prepare_equipment_brand_user_count(self, obj) -> int:
        return self._prepare_user_count(obj)

    def prepare_equipment_brand_image_count(self, obj) -> int:
        return self._prepare_image_count(obj)
