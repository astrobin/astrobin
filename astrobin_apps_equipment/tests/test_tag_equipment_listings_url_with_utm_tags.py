from django.test import TestCase

from astrobin_apps_equipment.templatetags.astrobin_apps_equipment_tags import equipment_listing_url_with_tags
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestTagEquipmentListingUrlWithUtmTags(TestCase):
    def test_simple_url(self):
        listing = EquipmentGenerators.equipment_brand_listing(url='https://www.example.com')
        self.assertEqual(
            f'https://www.example.com?brand={listing.brand.name}&retailer={listing.retailer.name}&source=foo',
            equipment_listing_url_with_tags(listing, 'foo')
        )

    def test_complex_url(self):
        listing = EquipmentGenerators.equipment_brand_listing(url='https://www.example.com/1/2/3/')
        self.assertEqual(
            f'https://www.example.com/1/2/3/?brand={listing.brand.name}&retailer={listing.retailer.name}&source=foo',
            equipment_listing_url_with_tags(listing, 'foo')
        )

    def test_url_with_params(self):
        listing = EquipmentGenerators.equipment_brand_listing(url='https://www.example.com/search?q=foo')
        self.assertEqual(
            f'https://www.example.com/search?q=foo&brand={listing.brand.name}&retailer={listing.retailer.name}&source=foo',
            equipment_listing_url_with_tags(listing, 'foo')
        )

    def test_url_with_conflicting_params(self):
        listing = EquipmentGenerators.equipment_brand_listing(url='https://www.example.com/search?q=foo&source=foo')
        self.assertEqual(
            'https://www.example.com/search?q=foo&source=foo',
            equipment_listing_url_with_tags(listing, 'bar')
        )
