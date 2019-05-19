# Django
from django.test import TestCase

# AstroBin
from utils import get_client_country_code


class UtilsTest(TestCase):
    def test_get_client_country_code    (self):
        self.assertEquals("US", get_client_country_code("www.astrobin.com"))
