from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models.camera_base_model import CameraType
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
        }, format='json')

        self.assertContains(response, "Modified cameras do not support edit proposals", status_code=400)
