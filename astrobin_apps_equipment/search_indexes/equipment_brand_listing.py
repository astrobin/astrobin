from haystack import fields
from haystack.constants import Indexable
from celery_haystack.indexes import CelerySearchIndex

from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from common.utils import get_segregated_reader_database


class EquipmentBrandListingIndex(CelerySearchIndex, Indexable):
    text = fields.CharField(document=True, use_template=True)
    countries = fields.CharField(model_attr="retailer__countries", null=True)

    def index_queryset(self, using=None):
        return self.get_model().objects.using(get_segregated_reader_database()).all()

    def get_model(self):
        return EquipmentBrandListing
