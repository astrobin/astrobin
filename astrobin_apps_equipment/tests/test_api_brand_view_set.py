from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestApiBrandViewSet(TestCase):
    def test_list_with_no_items(self):
        client = APIClient()

        response = client.get(reverse('astrobin_apps_equipment:brand-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_with_items(self):
        client = APIClient()

        brand = EquipmentGenerators.brand()

        response = client.get(reverse('astrobin_apps_equipment:brand-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(brand.name, response.data['results'][0]['name'])
