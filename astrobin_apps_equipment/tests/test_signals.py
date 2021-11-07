from django.test import TestCase

from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class SignalsTest(TestCase):
    def test_mirror_modified_camera(self):
        camera = EquipmentGenerators.camera()
        modified = EquipmentGenerators.camera(
            created_by=camera.created_by,
            brand=camera.brand,
            name=camera.name,
            image=camera.image,
            type=camera.type,
            sensor=camera.sensor,
            cooled=camera.cooled,
            max_cooling=camera.max_cooling,
            back_focus=camera.back_focus,
            modified=True,
        )

        camera.name = camera.name + ' updated'
        camera.save()

        modified = Camera.objects.get(pk=modified.pk)

        self.assertEqual(camera.name, modified.name)
