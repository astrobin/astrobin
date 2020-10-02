from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.templatetags.astrobin_apps_equipment_tags import equipment_brand_listings
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestTagEquipmentBrandListings(TestCase):
    def test_no_listings(self):
        telescope = Generators.telescope()
        self.assertEquals(0, equipment_brand_listings(telescope, 'us').count())

    def test_listing_in_wrong_country(self):
        listing = EquipmentGenerators.equipmentBrandListing()
        listing.retailer.countries = "it,ch,fi"
        listing.retailer.save()

        telescope = Generators.telescope()
        telescope.equipment_brand_listings.add(listing)

        self.assertEquals(0, equipment_brand_listings(telescope, 'us').count())

    def test_listing_correct_country(self):
        listing = EquipmentGenerators.equipmentBrandListing()
        listing.retailer.countries = "us"
        listing.retailer.save()

        telescope = Generators.telescope()
        telescope.equipment_brand_listings.add(listing)

        self.assertEquals(1, equipment_brand_listings(telescope, 'us').count())

    def test_listing_no_country(self):
        listing = EquipmentGenerators.equipmentBrandListing()

        telescope = Generators.telescope()
        telescope.equipment_brand_listings.add(listing)

        self.assertEquals(1, equipment_brand_listings(telescope, 'us').count())
