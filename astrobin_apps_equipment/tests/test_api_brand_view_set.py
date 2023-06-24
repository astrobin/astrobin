from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from common.constants import GroupName


class TestApiBrandViewSet(TestCase):
    def test_list_with_no_brands(self):
        client = APIClient()

        response = client.get(reverse('astrobin_apps_equipment:brand-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_with_no_equipment_items(self):
        client = APIClient()

        EquipmentGenerators.brand()

        response = client.get(reverse('astrobin_apps_equipment:brand-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_with_unapproved_equipment_items(self):
        client = APIClient()

        brand = EquipmentGenerators.brand()
        EquipmentGenerators.telescope(brand=brand)

        response = client.get(reverse('astrobin_apps_equipment:brand-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_with_approved_equipment_items(self):
        client = APIClient()

        brand = EquipmentGenerators.brand()
        EquipmentGenerators.telescope(brand=brand, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        response = client.get(reverse('astrobin_apps_equipment:brand-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(brand.name, response.data['results'][0]['name'])

    def test_deleting_not_allowed(self):
        client = APIClient()

        brand = EquipmentGenerators.brand()

        response = client.delete(reverse('astrobin_apps_equipment:brand-detail', args=(brand.pk,)), format='json')
        self.assertEquals(405, response.status_code)

        user = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.delete(reverse('astrobin_apps_equipment:brand-detail', args=(brand.pk,)), format='json')
        self.assertEquals(405, response.status_code)

    def test_post_not_allowed(self):
        client = APIClient()

        response = client.post(reverse('astrobin_apps_equipment:brand-list'), {
            'name': 'Foo',
            'website': 'https://www.foo.com/',
        }, format='json')
        self.assertEquals(403, response.status_code)

        user = Generators.user()
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(reverse('astrobin_apps_equipment:brand-list'), {
            'name': 'Foo',
            'website': 'https://www.foo.com/',
        }, format='json')
        self.assertEquals(403, response.status_code)

    def test_created_by(self):
        client = APIClient()

        user = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(reverse('astrobin_apps_equipment:brand-list'), {
            'name': 'Foo',
            'website': 'https://www.foo.com/',
        }, format='json')
        self.assertEquals(201, response.status_code)
        self.assertEquals(user.pk, response.data['created_by'])
