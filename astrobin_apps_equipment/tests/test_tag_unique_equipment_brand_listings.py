from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.templatetags.astrobin_apps_equipment_tags import unique_equipment_brand_listings
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestTagUniqueEquipmentBrandListings(TestCase):
    def test_no_listings(self):
        image = Generators.image()

        self.assertEquals(0, unique_equipment_brand_listings(image, 'us').count())

    def test_with_gear_but_no_listings(self):
        telescope = Generators.telescope()

        image = Generators.image()
        image.imaging_telescopes.add(telescope)

        self.assertEquals(0, unique_equipment_brand_listings(image, 'us').count())

    def test_with_gear_and_listing_in_wrong_country(self):
        listing = EquipmentGenerators.equipment_brand_listing()
        listing.retailer.countries = "ch"
        listing.retailer.save()

        telescope = Generators.telescope()
        telescope.equipment_brand_listings.add(listing)

        image = Generators.image()
        image.imaging_telescopes.add(telescope)

        self.assertEquals(0, unique_equipment_brand_listings(image, 'us').count())

    def test_with_gear_and_listing_in_no_country(self):
        listing = EquipmentGenerators.equipment_brand_listing()

        telescope = Generators.telescope()
        telescope.equipment_brand_listings.add(listing)

        image = Generators.image()
        image.imaging_telescopes.add(telescope)

        self.assertEquals(1, unique_equipment_brand_listings(image, 'us').count())

    def test_with_gear_and_listing_in_right_country(self):
        listing = EquipmentGenerators.equipment_brand_listing()
        listing.retailer.countries = "us"
        listing.retailer.save()

        telescope = Generators.telescope()
        telescope.equipment_brand_listings.add(listing)

        image = Generators.image()
        image.imaging_telescopes.add(telescope)

        self.assertEquals(1, unique_equipment_brand_listings(image, 'us').count())

    def test_with_gear_and_two_unique_listings_on_same_gear_in_right_country(self):
        listing1 = EquipmentGenerators.equipment_brand_listing()
        listing1.retailer.countries = "us"
        listing1.retailer.save()

        listing2 = EquipmentGenerators.equipment_brand_listing()
        listing2.retailer.countries = "us"
        listing2.retailer.save()

        telescope = Generators.telescope()
        telescope.equipment_brand_listings.add(listing1)
        telescope.equipment_brand_listings.add(listing2)

        image = Generators.image()
        image.imaging_telescopes.add(telescope)

        self.assertEquals(2, unique_equipment_brand_listings(image, 'us').count())

    def test_with_gear_and_two_unique_listings_on_different_gear_in_right_country(self):
        listing1 = EquipmentGenerators.equipment_brand_listing()
        listing1.retailer.countries = "us"
        listing1.retailer.save()

        listing2 = EquipmentGenerators.equipment_brand_listing()
        listing2.retailer.countries = "us"
        listing2.retailer.save()

        telescope = Generators.telescope()
        telescope.equipment_brand_listings.add(listing1)

        mount = Generators.mount()
        mount.equipment_brand_listings.add(listing2)

        image = Generators.image()
        image.imaging_telescopes.add(telescope)
        image.mounts.add(mount)

        self.assertEquals(2, unique_equipment_brand_listings(image, 'us').count())

    def test_with_gear_and_two_unique_listings_on_different_gear_from_same_retailer_in_right_country(self):
        listing1 = EquipmentGenerators.equipment_brand_listing()
        listing1.retailer.countries = "us"
        listing1.retailer.save()

        listing2 = EquipmentGenerators.equipment_brand_listing()
        listing2.retailer = listing1.retailer
        listing2.save()

        telescope = Generators.telescope()
        telescope.equipment_brand_listings.add(listing1)

        mount = Generators.mount()
        mount.equipment_brand_listings.add(listing2)

        image = Generators.image()
        image.imaging_telescopes.add(telescope)
        image.mounts.add(mount)

        self.assertEquals(2, unique_equipment_brand_listings(image, 'us').count())

    def test_with_gear_and_two_non_unique_listings_on_different_gear_in_right_country(self):
        listing = EquipmentGenerators.equipment_brand_listing()
        listing.retailer.countries = "us"
        listing.retailer.save()

        telescope = Generators.telescope()
        telescope.equipment_brand_listings.add(listing)

        mount = Generators.mount()
        mount.equipment_brand_listings.add(listing)

        image = Generators.image()
        image.imaging_telescopes.add(telescope)
        image.mounts.add(mount)

        self.assertEquals(1, unique_equipment_brand_listings(image, 'us').count())
