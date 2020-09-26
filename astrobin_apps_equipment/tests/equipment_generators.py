from django.template.defaultfilters import slugify

from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_retailer import EquipmentRetailer


class EquipmentGenerators:
    def __init__(self):
        pass

    @staticmethod
    def equipmentBrand():
        return EquipmentBrand.objects.create(
            name="Test brand"
        )

    @staticmethod
    def equipmentRetailer():
        return EquipmentRetailer.objects.create(
            name="Test retailer",
            website="https://www.test-retailer.com",
        )

    @staticmethod
    def equipmentBrandListing():
        brand = EquipmentGenerators.equipmentBrand()
        retailer = EquipmentGenerators.equipmentRetailer()

        return EquipmentBrandListing.objects.create(
            brand=brand,
            retailer=retailer,
            url="%s/shop/%s" % (retailer.website, slugify(brand)),
        )
