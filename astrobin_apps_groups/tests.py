# Django
from django.core.urlresolvers import reverse
from django.test import TestCase


class GroupsTest(TestCase):
    def test_public_group_list_view(self):
        response = self.client.get(reverse('public_group_list'))
        self.assertEqual(response.status_code, 200)
