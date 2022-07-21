from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import CameraEditProposal
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from common.constants import GroupName


class TestApiCameraEditProposalViewSet(TestCase):
    def test_edit_proposal_assignee_does_not_exist(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS]))

        camera = EquipmentGenerators.camera(
            type=CameraType.DEDICATED_DEEP_SKY,
            reviewer_decision=EquipmentItemReviewerDecision.APPROVED,
        )

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': EquipmentGenerators.brand().pk,
                'sensor': EquipmentGenerators.sensor().pk,
                'name': 'Camera Foo',
                'type': CameraType.DEDICATED_DEEP_SKY,
                'klass': camera.klass,
                'editProposalAssignee': 999
            }, format='json'
        )

        self.assertContains(response, "Invalid pk", status_code=400)

    def test_edit_proposal_assignee_is_not_creator_or_moderator(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS]))

        camera = EquipmentGenerators.camera(
            type=CameraType.DEDICATED_DEEP_SKY,
            reviewer_decision=EquipmentItemReviewerDecision.APPROVED,
        )

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': EquipmentGenerators.brand().pk,
                'sensor': EquipmentGenerators.sensor().pk,
                'name': 'Camera Foo',
                'type': CameraType.DEDICATED_DEEP_SKY,
                'klass': camera.klass,
                'editProposalAssignee': Generators.user().pk
            }, format='json'
        )

        self.assertContains(response, "An edit proposal can only be assigned", status_code=400)

    def test_assign_as_non_moderator(self):
        camera = EquipmentGenerators.camera(
            type=CameraType.DEDICATED_DEEP_SKY,
        )

        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS]))

        client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': EquipmentGenerators.brand().pk,
                'sensor': EquipmentGenerators.sensor().pk,
                'name': 'Camera Foo',
                'type': CameraType.DEDICATED_DEEP_SKY,
                'klass': camera.klass,
                'editProposalAssignee': Generators.user().pk
            }, format='json'
        )

        self.assertFalse(CameraEditProposal.objects.all().exists())

    def test_assign_to_unexistant_user(self):
        camera = EquipmentGenerators.camera(
            type=CameraType.DEDICATED_DEEP_SKY,
        )

        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS]))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': EquipmentGenerators.brand().pk,
                'sensor': EquipmentGenerators.sensor().pk,
                'name': 'Camera Foo',
                'type': CameraType.DEDICATED_DEEP_SKY,
                'klass': camera.klass,
                'editProposalAssignee': 999
            }, format='json'
        )

        self.assertContains(response, "Invalid pk", status_code=400)
        self.assertFalse(CameraEditProposal.objects.all().exists())

    def test_assign_to_non_moderator(self):
        camera = EquipmentGenerators.camera(
            type=CameraType.DEDICATED_DEEP_SKY,
        )

        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS]))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': EquipmentGenerators.brand().pk,
                'sensor': EquipmentGenerators.sensor().pk,
                'name': 'Camera Foo',
                'type': CameraType.DEDICATED_DEEP_SKY,
                'klass': camera.klass,
                'editProposalAssignee': Generators.user().pk
            }, format='json'
        )

        self.assertContains(
            response,
            "An edit proposal can only be assigned to a moderator or the",
            status_code=400
        )
        self.assertFalse(CameraEditProposal.objects.all().exists())

    def test_assign_to_item_creator_works(self):
        creator = Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS])
        camera = EquipmentGenerators.camera(
            type=CameraType.DEDICATED_DEEP_SKY,
            created_by=creator,
        )

        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS]))

        client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': EquipmentGenerators.brand().pk,
                'sensor': EquipmentGenerators.sensor().pk,
                'name': 'Camera Foo',
                'type': CameraType.DEDICATED_DEEP_SKY,
                'klass': camera.klass,
            }, format='json'
        )

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-detail', args=(1,)) + 'assign/',
            {'assignee': creator.pk},
            format='json'
        )

        self.assertEquals(200, response.status_code)
        camera.refresh_from_db()
        self.assertEquals(creator, CameraEditProposal.objects.get(pk=1).edit_proposal_assignee)

    def test_assign_to_item_moderator_works(self):
        creator = Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS])
        moderator = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        camera = EquipmentGenerators.camera(
            type=CameraType.DEDICATED_DEEP_SKY,
            created_by=creator,
        )

        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS]))

        client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': EquipmentGenerators.brand().pk,
                'sensor': EquipmentGenerators.sensor().pk,
                'name': 'Camera Foo',
                'type': CameraType.DEDICATED_DEEP_SKY,
                'klass': camera.klass,
            }, format='json'
        )

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-detail', args=(1,)) + 'assign/',
            {'assignee': moderator.pk},
            format='json'
        )

        self.assertEquals(200, response.status_code)
        camera.refresh_from_db()
        self.assertEquals(moderator, CameraEditProposal.objects.get(pk=1).edit_proposal_assignee)


    def test_assign_to_edit_proposal_creator(self):
        edit_proposal_creator = Generators.user(groups=[GroupName.OWN_EQUIPMENT_MIGRATORS])
        camera = EquipmentGenerators.camera(
            type=CameraType.DEDICATED_DEEP_SKY,
            created_by=edit_proposal_creator
        )

        client = APIClient()
        client.force_authenticate(user=edit_proposal_creator)

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': EquipmentGenerators.brand().pk,
                'sensor': EquipmentGenerators.sensor().pk,
                'name': 'Camera Foo',
                'type': CameraType.DEDICATED_DEEP_SKY,
                'klass': camera.klass,
                'editProposalAssignee': edit_proposal_creator.pk
            }, format='json'
        )

        self.assertContains(response, "An edit proposal cannot be assigned to its creator", status_code=400)
