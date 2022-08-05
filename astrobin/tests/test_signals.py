import time
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from mock import patch

from astrobin.models import Image
from astrobin.signals import imagerevision_post_save
from astrobin.tests.generators import Generators
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class SignalsTest(TestCase):

    @patch("astrobin.signals.push_notification")
    @patch("astrobin.signals.add_story")
    def test_imagerevision_post_save_wip_no_notifications(self, add_story, push_notification):
        revision = Generators.imageRevision()
        revision.image.is_wip = True

        push_notification.reset_mock()
        add_story.reset_mock()

        imagerevision_post_save(None, revision, True)

        self.assertFalse(push_notification.called)
        self.assertFalse(add_story.called)

    @patch("astrobin.signals.push_notification")
    @patch("astrobin.signals.add_story")
    def test_imagerevision_post_save_not_created_no_notifications(self, add_story, push_notification):
        revision = Generators.imageRevision()

        push_notification.reset_mock()
        add_story.reset_mock()

        imagerevision_post_save(None, revision, False)

        self.assertFalse(push_notification.called)
        self.assertFalse(add_story.called)

    @patch("astrobin.signals.push_notification")
    @patch("astrobin.signals.add_story")
    def test_imagerevision_post_save_skip_notifications(self, add_story, push_notification):
        revision = Generators.imageRevision()
        revision.skip_notifications = True

        push_notification.reset_mock()
        add_story.reset_mock()

        imagerevision_post_save(None, revision, True)

        self.assertFalse(push_notification.called)
        self.assertFalse(add_story.called)

    @patch("astrobin.signals.push_notification")
    @patch("astrobin.signals.add_story")
    def test_imagerevision_post_save_uploading(self, add_story, push_notification):
        revision = Generators.imageRevision()
        revision.uploader_in_progress = True

        push_notification.reset_mock()
        add_story.reset_mock()

        imagerevision_post_save(None, revision, True)

        self.assertFalse(push_notification.called)
        self.assertFalse(add_story.called)

    @patch("astrobin.signals.add_story")
    def test_imagerevision_post_save(self, add_story):
        revision = Generators.imageRevision()

        add_story.reset_mock()

        imagerevision_post_save(None, revision, True)

        self.assertTrue(add_story.called)

    def test_imaging_telescope_change_causes_image_to_be_saved(self):
        image = Generators.image()
        telescope = Generators.telescope()

        before = image.updated
        time.sleep(0.01)

        image.imaging_telescopes.add(telescope)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_guiding_telescope_change_causes_image_to_be_saved(self):
        image = Generators.image()
        telescope = Generators.telescope()

        before = image.updated
        time.sleep(0.01)

        image.guiding_telescopes.add(telescope)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_imaging_camera_change_causes_image_to_be_saved(self):
        image = Generators.image()
        camera = Generators.camera()

        before = image.updated
        time.sleep(0.01)

        image.imaging_cameras.add(camera)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_guiding_camera_change_causes_image_to_be_saved(self):
        image = Generators.image()
        camera = Generators.camera()

        before = image.updated
        time.sleep(0.01)

        image.guiding_cameras.add(camera)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_mount_change_causes_image_to_be_saved(self):
        image = Generators.image()
        mount = Generators.mount()

        before = image.updated
        time.sleep(0.01)

        image.mounts.add(mount)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_filter_change_causes_image_to_be_saved(self):
        image = Generators.image()
        filter = Generators.filter()

        before = image.updated
        time.sleep(0.01)

        image.filters.add(filter)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_focal_reducer_change_causes_image_to_be_saved(self):
        image = Generators.image()
        focal_reducer = Generators.focal_reducer()

        before = image.updated
        time.sleep(0.01)

        image.focal_reducers.add(focal_reducer)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_accessory_change_causes_image_to_be_saved(self):
        image = Generators.image()
        accessory = Generators.accessory()

        before = image.updated
        time.sleep(0.01)

        image.accessories.add(accessory)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_software_change_causes_image_to_be_saved(self):
        image = Generators.image()
        software = Generators.software()

        before = image.updated
        time.sleep(0.01)

        image.software.add(software)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_imaging_telescope_2_change_causes_image_to_be_saved(self):
        image = Generators.image()
        telescope = EquipmentGenerators.telescope()

        Image.objects.filter(pk=image.pk).update(updated=timezone.now() - timedelta(minutes=1))
        image.refresh_from_db()

        before = image.updated
        time.sleep(0.01)

        image.imaging_telescopes_2.add(telescope)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_guiding_telescope_2_change_causes_image_to_be_saved(self):
        image = Generators.image()
        telescope = EquipmentGenerators.telescope()

        Image.objects.filter(pk=image.pk).update(updated=timezone.now() - timedelta(minutes=1))
        image.refresh_from_db()

        before = image.updated
        time.sleep(0.01)

        image.guiding_telescopes_2.add(telescope)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_imaging_camera_2_change_causes_image_to_be_saved(self):
        image = Generators.image()
        camera = EquipmentGenerators.camera()

        Image.objects.filter(pk=image.pk).update(updated=timezone.now() - timedelta(minutes=1))
        image.refresh_from_db()

        before = image.updated
        time.sleep(0.01)

        image.imaging_cameras_2.add(camera)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_guiding_camera_2_change_causes_image_to_be_saved(self):
        image = Generators.image()
        camera = EquipmentGenerators.camera()

        Image.objects.filter(pk=image.pk).update(updated=timezone.now() - timedelta(minutes=1))
        image.refresh_from_db()

        before = image.updated
        time.sleep(0.01)

        image.guiding_cameras_2.add(camera)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_mount_2_change_causes_image_to_be_saved(self):
        image = Generators.image()
        mount = EquipmentGenerators.mount()

        Image.objects.filter(pk=image.pk).update(updated=timezone.now() - timedelta(minutes=1))
        image.refresh_from_db()

        before = image.updated
        time.sleep(0.01)

        image.mounts_2.add(mount)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_filter_2_change_causes_image_to_be_saved(self):
        image = Generators.image()
        filter = EquipmentGenerators.filter()

        Image.objects.filter(pk=image.pk).update(updated=timezone.now() - timedelta(minutes=1))
        image.refresh_from_db()

        before = image.updated
        time.sleep(0.01)

        image.filters_2.add(filter)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)


    def test_accessory_2_change_causes_image_to_be_saved(self):
        image = Generators.image()
        accessory = EquipmentGenerators.accessory()

        Image.objects.filter(pk=image.pk).update(updated=timezone.now() - timedelta(minutes=1))
        image.refresh_from_db()

        before = image.updated
        time.sleep(0.01)

        image.accessories_2.add(accessory)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)

    def test_software_2_change_causes_image_to_be_saved(self):
        image = Generators.image()
        software = EquipmentGenerators.software()

        Image.objects.filter(pk=image.pk).update(updated=timezone.now() - timedelta(minutes=1))
        image.refresh_from_db()

        before = image.updated
        time.sleep(0.01)

        image.software_2.add(software)

        image.refresh_from_db()

        self.assertGreater(image.updated, before)
