from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from common.constants import GroupName


class TestApiCameraViewSetQueryset(TestCase):
    def test_list_with_no_items(self):
        client = APIClient()

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_with_items(self):
        client = APIClient()

        camera = EquipmentGenerators.camera(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(camera.name, response.data['results'][0]['name'])

    def test_unapproved_item_not_returned_if_anon(self):
        client = APIClient()

        EquipmentGenerators.camera()

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_unapproved_item_not_returned_if_non_moderator(self):
        client = APIClient()

        EquipmentGenerators.camera()

        client.force_authenticate(user=Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_unapproved_item_returned_if_creator(self):
        client = APIClient()

        creator = Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS])
        EquipmentGenerators.camera(created_by=creator)

        client.force_authenticate(user=creator)

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(1, response.data['count'])

    def test_unapproved_item_returned_if_moderator(self):
        client = APIClient()

        EquipmentGenerators.camera()

        client.force_authenticate(user=Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(1, response.data['count'])

    def test_approved_item_not_returned_if_diy(self):
        client = APIClient()

        EquipmentGenerators.camera(brand=None, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        client.force_authenticate(user=Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_approved_item_returned_if_diy_and_moderator(self):
        client = APIClient()

        EquipmentGenerators.camera(brand=None, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        client.force_authenticate(user=Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(1, response.data['count'])

    def test_approved_item_returned_if_diy_and_creator(self):
        client = APIClient()


        creator = Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS])
        EquipmentGenerators.camera(created_by=creator, brand=None, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        client.force_authenticate(user=creator)

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(1, response.data['count'])

    def test_approved_item_not_returned_if_frozen_and_anon(self):
        client = APIClient()

        EquipmentGenerators.camera(frozen_as_ambiguous=True, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_approved_item_not_returned_if_frozen_and_non_moderator(self):
        client = APIClient()

        EquipmentGenerators.camera(frozen_as_ambiguous=True, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        client.force_authenticate(user=Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_approved_item_returned_if_frozen_and_moderator(self):
        client = APIClient()

        EquipmentGenerators.camera(frozen_as_ambiguous=True, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        client.force_authenticate(user=Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(1, response.data['count'])

    def test_approved_item_not_returned_if_frozen_and_creator(self):
        client = APIClient()

        creator = Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS])
        EquipmentGenerators.camera(created_by=creator, frozen_as_ambiguous=True, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        client.force_authenticate(user=creator)

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_variants_are_included(self):
        client = APIClient()

        camera = EquipmentGenerators.camera(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        EquipmentGenerators.camera(reviewer_decision=EquipmentItemReviewerDecision.APPROVED, variant_of=camera)

        client.force_authenticate(user=Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(2, response.data['count'])

    def test_variants_are_not_included(self):
        client = APIClient()

        camera = EquipmentGenerators.camera(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        EquipmentGenerators.camera(reviewer_decision=EquipmentItemReviewerDecision.APPROVED, variant_of=camera)

        client.force_authenticate(user=Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list') + '?include-variants=false', format='json')
        self.assertEquals(1, response.data['count'])

    def test_query_with_exact_brand_only_shows_items_from_that_brand(self):
        client = APIClient()

        brand1 = EquipmentGenerators.brand(name="foo")
        brand2 = EquipmentGenerators.brand(name="bar")

        camera1 = EquipmentGenerators.camera(brand=brand1, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        EquipmentGenerators.camera(brand=brand2, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        client.force_authenticate(user=Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list') + f'?q={brand1.name}', format='json')

        self.assertEquals(1, response.data['count'])
        self.assertEquals(camera1.id, response.data['results'][0]['id'])

    def test_query_with_exact_brand_only_shows_items_from_that_brand_except_if_unapproved(self):
        client = APIClient()

        brand1 = EquipmentGenerators.brand(name="foo")
        brand2 = EquipmentGenerators.brand(name="bar")

        EquipmentGenerators.camera(brand=brand1)
        EquipmentGenerators.camera(brand=brand2, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        client.force_authenticate(user=Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list') + f'?q={brand1.name}', format='json')

        self.assertEquals(0, response.data['count'])

    def test_query_with_exact_brand_only_shows_items_from_that_brand_except_if_unapproved_except_if_moderator(self):
        client = APIClient()

        brand1 = EquipmentGenerators.brand(name="foo")
        brand2 = EquipmentGenerators.brand(name="bar")

        camera1 = EquipmentGenerators.camera(brand=brand1)
        EquipmentGenerators.camera(brand=brand2, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        client.force_authenticate(user=Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS]))

        response = client.get(reverse('astrobin_apps_equipment:camera-list') + f'?q={brand1.name}', format='json')

        self.assertEquals(1, response.data['count'])
        self.assertEquals(camera1.id, response.data['results'][0]['id'])
