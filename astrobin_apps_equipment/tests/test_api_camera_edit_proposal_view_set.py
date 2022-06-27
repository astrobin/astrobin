from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestApiCameraEditProposalViewSet(TestCase):
    def test_not_allowed_for_modified_camera(self):
        user = Generators.user(groups=['equipment_moderators'])
        client = APIClient()
        client.force_authenticate(user=user)

        camera = EquipmentGenerators.camera(modified=True)

        response = client.post(reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
            'editProposalTarget': camera.pk,
            'brand': EquipmentGenerators.brand().pk,
            'sensor': EquipmentGenerators.sensor().pk,
            'name': 'Camera Foo',
            'type': CameraType.DEDICATED_DEEP_SKY,
        }, format='json'
        )

        self.assertContains(
            response,
            "Modified and/or cooled DSLR or mirrorless cameras do not support edit proposals",
            status_code=400
        )

    def test_klass_mismatch(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        camera = EquipmentGenerators.camera()

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'name': camera.name,
                'type': camera.type,
                'klass': EquipmentItemKlass.TELESCOPE,
            },
            format='json'
        )

        self.assertContains(response, "The klass property must match that of the target item", status_code=400)

    def test_edit_proposal_review_status_must_be_null(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        camera = EquipmentGenerators.camera()

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'name': camera.name,
                'type': camera.type,
                'klass': camera.klass,
                'editProposalReviewStatus': 'APPROVED',
            },
            format='json'
        )

        self.assertContains(response, "The edit_proposal_review_status must be null", status_code=400)

    def test_already_has_pending(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        camera = EquipmentGenerators.camera()

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'name': camera.name,
                'type': camera.type,
                'klass': camera.klass,
            },
            format='json'
        )

        self.assertEqual(201, response.status_code)

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'name': camera.name,
                'type': camera.type,
                'klass': camera.klass,
            },
            format='json'
        )

        self.assertContains(response, "This item already has a pending edit proposal", status_code=400)

    def test_brand_and_variant_of_brand_mismatch(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        brand1 = EquipmentGenerators.brand()
        brand2 = EquipmentGenerators.brand()
        camera = EquipmentGenerators.camera(brand=brand1)

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'name': camera.name,
                'type': camera.type,
                'klass': camera.klass,
                'variant_of': EquipmentGenerators.camera(brand=brand2).pk
            },
            format='json'
        )

        self.assertContains(response, "The variant needs to be in the same brand as the item", status_code=400)

    def test_diy_does_not_allow_variants(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        camera = EquipmentGenerators.camera(brand=None)

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': None,
                'name': camera.name,
                'type': camera.type,
                'klass': camera.klass,
                'variant_of': EquipmentGenerators.camera().pk
            },
            format='json'
        )

        self.assertContains(response, "DIY items do not support variants", status_code=400)

    def test_circular_variants(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        brand = EquipmentGenerators.brand()
        camera = EquipmentGenerators.camera(brand=brand)
        variant = EquipmentGenerators.camera(brand=brand, variant_of=camera)

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'name': camera.name,
                'type': camera.type,
                'klass': camera.klass,
                'variant_of': variant.pk
            },
            format='json'
        )

        self.assertContains(response, "Variants do not support variants", status_code=400)

    def test_self_variant(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        brand = EquipmentGenerators.brand()
        camera = EquipmentGenerators.camera(brand=brand)

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'name': camera.name,
                'type': camera.type,
                'klass': camera.klass,
                'variant_of': camera.pk
            },
            format='json'
        )

        self.assertContains(response, "An item cannot be a variant of itself", status_code=400)

    def test_dslr_mirrorless_does_not_allow_variants(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        camera = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS)
        camera2 = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS)

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'type': camera.type,
                'name': camera.name,
                'klass': camera.klass,
                'variant_of': camera2.pk
            },
            format='json'
        )

        self.assertContains(response, "DSLR/Mirrorless cameras do not support variants", status_code=400)

    def test_name_change_requires_moderator(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['own_equipment_migrators']))

        camera = EquipmentGenerators.camera(
            type=CameraType.DEDICATED_DEEP_SKY,
            reviewer_decision=EquipmentItemReviewerDecision.APPROVED
        )

        client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'type': camera.type,
                'name': camera.name + " 2",
                'klass': camera.klass,
            },
            format='json'
        )

        client.force_authenticate(user=Generators.user(groups=['own_equipment_migrators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list') + '1/approve/', {}, format='json'
        )

        self.assertContains(response, "This edit proposal needs to be approved by a moderator", status_code=403)

        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list') + '1/approve/', {}, format='json'
        )

        self.assertEquals(200, response.status_code)

    def test_name_change_does_not_moderator_when_created_by_moderator(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        camera = EquipmentGenerators.camera(
            type=CameraType.DEDICATED_DEEP_SKY,
            reviewer_decision=EquipmentItemReviewerDecision.APPROVED
        )

        client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'type': camera.type,
                'name': camera.name + " 2",
                'klass': camera.klass,
            },
            format='json'
        )

        client.force_authenticate(user=Generators.user(groups=['own_equipment_migrators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list') + '1/approve/', {}, format='json'
        )

        self.assertEquals(200, response.status_code)

    def test_name_change_does_not_moderator_when_item_is_unapproved(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['own_equipment_migrators']))

        camera = EquipmentGenerators.camera(type=CameraType.DEDICATED_DEEP_SKY, reviewer_decision=None)

        client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list'), {
                'editProposalTarget': camera.pk,
                'brand': camera.brand.pk,
                'type': camera.type,
                'name': camera.name + " 2",
                'klass': camera.klass,
            },
            format='json'
        )

        client.force_authenticate(user=Generators.user(groups=['own_equipment_migrators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-edit-proposal-list') + '1/approve/', {}, format='json'
        )

        self.assertEquals(200, response.status_code)
