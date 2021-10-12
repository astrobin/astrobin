from django.test import TestCase

from astrobin_apps_equipment.templatetags.astrobin_apps_equipment_tags import equipment_listing_url_with_utm_tags


class TestTagEquipmentListingUrlWithUtmTags(TestCase):
    def test_simple_url(self):
        url = equipment_listing_url_with_utm_tags('https://www.example.com')
        self.assertEqual(
            'https://www.example.com?utm_source=astrobin&utm_medium=link&utm_campaign=webshop-integration',
            url
        )

    def test_complex_url(self):
        url = equipment_listing_url_with_utm_tags('https://www.example.com/1/2/3/')
        self.assertEqual(
            'https://www.example.com/1/2/3/?utm_source=astrobin&utm_medium=link&utm_campaign=webshop-integration',
            url
        )

    def test_url_with_params(self):
        url = equipment_listing_url_with_utm_tags('https://www.example.com/search?q=foo')
        self.assertEqual(
            'https://www.example.com/search?q=foo&utm_source=astrobin&utm_medium=link&utm_campaign=webshop-integration',
            url
        )

    def test_url_with_utm_params(self):
        url = equipment_listing_url_with_utm_tags('https://www.example.com/search?q=foo&utm_source=foo')
        self.assertEqual('https://www.example.com/search?q=foo&utm_source=foo', url)
