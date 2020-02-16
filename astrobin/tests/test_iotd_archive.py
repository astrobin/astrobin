from django.core.urlresolvers import reverse
from django.test import TestCase


class IOTDArchiveTest(TestCase):
    def test_page_exists(self):
        response = self.client.get(reverse('iotd_archive'))
        self.assertEqual(response.status_code, 200)
