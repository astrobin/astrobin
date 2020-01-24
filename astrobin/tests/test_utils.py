from mock import patch

# Django
from django.test import TestCase

# AstroBin
from astrobin.utils import get_client_country_code


class UtilsTest(TestCase):
    @patch("astrobin.utils.get_client_ip")
    @patch("django.contrib.gis.geoip2.GeoIP2.country_code")
    def test_get_client_country_code(self, mock_country, mock_get_client_ip):
        mock_country.return_value = "CH"
        mock_get_client_ip.return_value = "123.123.123.123"

        self.assertEquals("CH", get_client_country_code(None))
