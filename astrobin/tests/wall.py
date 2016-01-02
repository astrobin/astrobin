# Django
from django.core.urlresolvers import reverse
from django.test import TestCase

class WallTest(TestCase):
    def test_page_exists(self):
        response = self.client.get(reverse('wall'))
        self.assertEqual(response.status_code, 200)
