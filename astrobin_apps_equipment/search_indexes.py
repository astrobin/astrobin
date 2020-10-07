from celery_haystack.indexes import CelerySearchIndex
from haystack import fields
from haystack.constants import Indexable

from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing


class EquipmentBrandListingIndex(CelerySearchIndex, Indexable):
    text = fields.CharField(document=True, use_template=True)
    countries = fields.CharField(model_attr="retailer__countries")

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_model(self):
        return EquipmentBrandListing
