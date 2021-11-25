from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models.telescope_base_model import TelescopeType
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestApiTelescopeViewSet(TestCase):
    def test_list_with_no_items(self):
        client = APIClient()

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_with_items(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope()

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(telescope.name, response.data['results'][0]['name'])

    def test_deleting_not_allowed(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope()

        response = client.delete(reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)), format='json')
        self.assertEquals(405, response.status_code)

        user = Generators.user(groups=['equipment_moderators'])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.delete(reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)), format='json')
        self.assertEquals(405, response.status_code)

    def test_post_not_allowed(self):
        client = APIClient()

        response = client.post(reverse('astrobin_apps_equipment:telescope-list'), {
            'brand': EquipmentGenerators.brand().pk,
            'name': 'telescope Foo',
            'type': TelescopeType.REFRACTOR_ACHROMATIC,
        }, format='json')
        self.assertEquals(403, response.status_code)

        user = Generators.user()
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(reverse('astrobin_apps_equipment:telescope-list'), {
            'brand': EquipmentGenerators.brand().pk,
            'name': 'telescope Foo',
            'type': TelescopeType.REFRACTOR_ACHROMATIC,
        }, format='json')
        self.assertEquals(403, response.status_code)

    def test_created_by(self):
        client = APIClient()

        user = Generators.user(groups=['equipment_moderators'])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(reverse('astrobin_apps_equipment:telescope-list'), {
            'brand': EquipmentGenerators.brand().pk,
            'name': 'telescope Foo',
            'type': TelescopeType.REFRACTOR_ACHROMATIC,
        }, format='json')
        self.assertEquals(201, response.status_code)
        self.assertEquals(user.pk, response.data['created_by'])

    def test_list_returns_only_own_DIYs(self):
        user = Generators.user()
        first = EquipmentGenerators.telescope(created_by=user)
        first.brand = None
        first.save()

        second = EquipmentGenerators.telescope()
        second.brand = None
        second.save()

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(first.name, response.data['results'][0]['name'])


