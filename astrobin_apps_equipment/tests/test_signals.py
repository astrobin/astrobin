from django.test import TestCase

from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
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

    def test_mirror_modified_camera_deletion(self):
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

        camera.delete()

        self.assertFalse(Camera.objects.filter(pk=modified.pk).exists())

    def test_remove_sensor_from_cameras_after_deletion(self):
        camera = EquipmentGenerators.camera()
        camera.sensor.delete()
        camera = Camera.objects.get(pk=camera.pk)

        self.assertIsNone(camera.sensor)

    def test_forum_creation(self):
        telescope = EquipmentGenerators.telescope()
        self.assertIsNone(telescope.forum)

        telescope.reviewer_decision = EquipmentItemReviewerDecision.APPROVED
        telescope.save()
        telescope.refresh_from_db()

        self.assertIsNotNone(telescope.forum)

    def test_forum_deletion(self):
        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        self.assertIsNotNone(telescope.forum)

        telescope.reviewer_decision = EquipmentItemReviewerDecision.REJECTED
        telescope.save()
        telescope.refresh_from_db()

        self.assertIsNone(telescope.forum)
