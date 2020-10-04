from django.template.defaultfilters import slugify

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_item_listing import EquipmentItemListing
from astrobin_apps_equipment.models.equipment_retailer import EquipmentRetailer


class EquipmentGenerators:
    def __init__(self):
        pass

    @staticmethod
    def equipment_brand():
        return EquipmentBrand.objects.create(
            name=Generators.randomString()
        )

    @staticmethod
    def equipment_retailer():
        return EquipmentRetailer.objects.create(
            name=Generators.randomString(),
            website="https://www.%s.com" % Generators.randomString(),
        )

    @staticmethod
    def equipment_brand_listing():
        brand = EquipmentGenerators.equipment_brand()
        retailer = EquipmentGenerators.equipment_retailer()

        return EquipmentBrandListing.objects.create(
            brand=brand,
            retailer=retailer,
            url="%s/shop/%s" % (retailer.website, slugify(brand)),
        )

    @staticmethod
    def equipment_item_listing():
        brand = EquipmentGenerators.equipment_brand()
        retailer = EquipmentGenerators.equipment_retailer()

        return EquipmentItemListing.objects.create(
            name=Generators.randomString(),
            retailer=retailer,
            url="%s/shop/%s" % (retailer.website, slugify(brand)),
        )
