from haystack import fields
from haystack.constants import Indexable
from haystack.indexes import SearchIndex

from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing


class EquipmentBrandListingIndex(SearchIndex, Indexable):
    text = fields.CharField(document=True, use_template=True)
    countries = fields.CharField(model_attr="retailer__countries", null=True)

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_model(self):
        return EquipmentBrandListing
