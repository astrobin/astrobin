from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.models.filter_base_model import FilterType
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from common.constants import GroupName


class TestApiFilterViewSet(TestCase):
    def test_list_with_no_items(self):
        client = APIClient()

        response = client.get(reverse('astrobin_apps_equipment:filter-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_with_items(self):
        client = APIClient()

        filter = EquipmentGenerators.filter(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        response = client.get(reverse('astrobin_apps_equipment:filter-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(filter.name, response.data['results'][0]['name'])

    def test_deleting_not_allowed(self):
        client = APIClient()

        filter = EquipmentGenerators.filter()

        response = client.delete(reverse('astrobin_apps_equipment:filter-detail', args=(filter.pk,)), format='json')
        self.assertEquals(405, response.status_code)

        user = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.delete(reverse('astrobin_apps_equipment:filter-detail', args=(filter.pk,)), format='json')
        self.assertEquals(405, response.status_code)

    def test_post_not_allowed(self):
        client = APIClient()

        response = client.post(reverse('astrobin_apps_equipment:filter-list'), {
            'brand': EquipmentGenerators.brand().pk,
            'name': 'filter Foo',
            'type': FilterType.L,
        }, format='json')
        self.assertEquals(403, response.status_code)

        user = Generators.user()
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(reverse('astrobin_apps_equipment:filter-list'), {
            'brand': EquipmentGenerators.brand().pk,
            'name': 'filter Foo',
            'type': FilterType.L,
        }, format='json')
        self.assertEquals(403, response.status_code)

    def test_created_by(self):
        client = APIClient()

        user = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(reverse('astrobin_apps_equipment:filter-list'), {
            'brand': EquipmentGenerators.brand().pk,
            'name': 'filter Foo',
            'type': FilterType.L,
        }, format='json')
        self.assertEquals(201, response.status_code)
        self.assertEquals(user.pk, response.data['created_by'])

    def test_list_returns_only_own_DIYs(self):
        user = Generators.user()
        first = EquipmentGenerators.filter(created_by=user)
        first.brand = None
        first.save()

        second = EquipmentGenerators.filter()
        second.brand = None
        second.save()

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse('astrobin_apps_equipment:filter-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(first.name, response.data['results'][0]['name'])

    def test_find_recently_used_no_usages(self):
        user = Generators.user()

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:filter-list') + 'recently-used/', format='json'
        )

        self.assertEquals(0, len(response.data))

    def test_find_recently_used_one_usage(self):
        user = Generators.user()
        filter = EquipmentGenerators.filter(created_by=user)
        image = Generators.image(user=user)
        image.filters_2.add(filter)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:filter-list') + 'recently-used/', format='json'
        )

        self.assertEquals(1, len(response.data))


