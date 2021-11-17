from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestApiEquipmentItemGroupViewSet(TestCase):
    def test_list_with_no_items(self):
        client = APIClient()

        response = client.get(reverse('astrobin_apps_equipment:equipment-item-group-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_with_items(self):
        client = APIClient()

        group = EquipmentGenerators.equipment_item_group()
        
        telescope1 = EquipmentGenerators.telescope()
        telescope1.group = group
        telescope1.save()

        telescope2 = EquipmentGenerators.telescope()
        telescope2.group = group
        telescope2.save()

        response = client.get(reverse('astrobin_apps_equipment:equipment-item-group-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(group.name, response.data['results'][0]['name'])
        self.assertEquals(2, len(response.data['results'][0]['telescope_set']))

    def test_deleting_not_allowed(self):
        client = APIClient()

        group = EquipmentGenerators.equipment_item_group()

        response = client.delete(reverse('astrobin_apps_equipment:equipment-item-group-detail', args=(group.pk,)), format='json')
        self.assertEquals(401, response.status_code)

        user = Generators.user(groups=['equipment_moderators'])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.delete(reverse('astrobin_apps_equipment:equipment-item-group-detail', args=(group.pk,)), format='json')
        self.assertEquals(403, response.status_code)

    def test_post_not_allowed(self):
        client = APIClient()

        response = client.post(reverse('astrobin_apps_equipment:equipment-item-group-list'), {
            'klass': EquipmentItemKlass.TELESCOPE,
            'name': 'Group Foo',
        }, format='json')
        self.assertEquals(401, response.status_code)

        user = Generators.user()
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(reverse('astrobin_apps_equipment:equipment-item-group-list'), {
            'klass': EquipmentItemKlass.TELESCOPE,
            'name': 'Group Foo',
        }, format='json')
        self.assertEquals(403, response.status_code)
