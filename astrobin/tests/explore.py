# Django
from django.core.urlresolvers import reverse
from django.test import TestCase

class ExploreTest(TestCase):
    def test_page_exists(self):
        response = self.client.get(reverse('explore_choose'))
        self.assertEqual(response.status_code, 200)
