from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.templatetags.astrobin_apps_equipment_tags import equipment_brand_listings, \
    equipment_listing_url_with_utm_tags
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestTagEquipmentListingUrlWithUtmTags(TestCase):
    def test_simple_url(self):
        url = equipment_listing_url_with_utm_tags('https://www.example.com')
        self.assertEquals(
            'https://www.example.com?utm_source=astrobin&utm_medium=link&utm_campaign=webshop-integration',
            url
        )

    def test_complex_url(self):
        url = equipment_listing_url_with_utm_tags('https://www.example.com/1/2/3/')
        self.assertEquals(
            'https://www.example.com/1/2/3/?utm_source=astrobin&utm_medium=link&utm_campaign=webshop-integration',
            url
        )

    def test_url_with_params(self):
        url = equipment_listing_url_with_utm_tags('https://www.example.com/search?q=foo')
        self.assertEquals(
            'https://www.example.com/search?q=foo&utm_source=astrobin&utm_medium=link&utm_campaign=webshop-integration',
            url
        )
