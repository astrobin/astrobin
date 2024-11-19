from django.test import TestCase

from astrobin.models import Image
from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import (
    EquipmentPreset,
)
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class EquipmentServiceFindImagesFeaturingPresetTest(TestCase):
    def test_find_images_featuring_preset_basic_match(self):
        user = Generators.user()
        telescope = EquipmentGenerators.telescope()
        camera = EquipmentGenerators.camera()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope)
        preset.imaging_cameras.add(camera)

        matching_image = Generators.image(user=user)
        matching_image.imaging_telescopes_2.add(telescope)
        matching_image.imaging_cameras_2.add(camera)

        non_matching_image = Generators.image(user=user)

        results = EquipmentService.find_images_featuring_preset(preset, Image.objects.all())
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), matching_image)

    def test_find_images_featuring_preset_no_equipment_specified(self):
        user = Generators.user()
        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )

        image1 = Generators.image(user=user)
        image2 = Generators.image(user=user)

        results = EquipmentService.find_images_featuring_preset(preset, Image.objects.all())
        self.assertEqual(results.count(), Image.objects.count())  # Should return all images

    def test_find_images_featuring_preset_multiple_equipment_options(self):
        user = Generators.user()
        telescope1 = EquipmentGenerators.telescope()
        telescope2 = EquipmentGenerators.telescope()
        camera = EquipmentGenerators.camera()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope1, telescope2)
        preset.imaging_cameras.add(camera)

        # Image with first telescope
        image1 = Generators.image(user=user)
        image1.imaging_telescopes_2.add(telescope1)
        image1.imaging_cameras_2.add(camera)

        # Image with second telescope
        image2 = Generators.image(user=user)
        image2.imaging_telescopes_2.add(telescope2)
        image2.imaging_cameras_2.add(camera)

        # Non-matching image
        image3 = Generators.image(user=user)

        results = EquipmentService.find_images_featuring_preset(preset, Image.objects.all())
        self.assertEqual(results.count(), 2)
        self.assertIn(image1, results)
        self.assertIn(image2, results)

    def test_find_images_featuring_preset_partial_matches(self):
        user = Generators.user()
        telescope = EquipmentGenerators.telescope()
        camera = EquipmentGenerators.camera()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope)
        preset.imaging_cameras.add(camera)

        # Image with just telescope
        partial_match = Generators.image(user=user)
        partial_match.imaging_telescopes_2.add(telescope)

        results = EquipmentService.find_images_featuring_preset(preset, Image.objects.all())
        self.assertEqual(results.count(), 0)

    def test_find_images_featuring_preset_all_equipment_types(self):
        user = Generators.user()
        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )

        # Create one of each equipment type
        telescope = EquipmentGenerators.telescope()
        guiding_telescope = EquipmentGenerators.telescope()
        mount = EquipmentGenerators.mount()
        camera = EquipmentGenerators.camera()
        guiding_camera = EquipmentGenerators.camera()
        filter_ = EquipmentGenerators.filter()
        accessory = EquipmentGenerators.accessory()
        software = EquipmentGenerators.software()

        # Add all equipment to preset
        preset.imaging_telescopes.add(telescope)
        preset.guiding_telescopes.add(guiding_telescope)
        preset.mounts.add(mount)
        preset.imaging_cameras.add(camera)
        preset.guiding_cameras.add(guiding_camera)
        preset.filters.add(filter_)
        preset.accessories.add(accessory)
        preset.software.add(software)

        # Create fully matching image
        matching_image = Generators.image(user=user)
        matching_image.imaging_telescopes_2.add(telescope)
        matching_image.guiding_telescopes_2.add(guiding_telescope)
        matching_image.mounts_2.add(mount)
        matching_image.imaging_cameras_2.add(camera)
        matching_image.guiding_cameras_2.add(guiding_camera)
        matching_image.filters_2.add(filter_)
        matching_image.accessories_2.add(accessory)
        matching_image.software_2.add(software)

        results = EquipmentService.find_images_featuring_preset(preset, Image.objects.all())
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), matching_image)

    def test_find_images_featuring_preset_queryset_filter(self):
        user1 = Generators.user()
        user2 = Generators.user()
        telescope = EquipmentGenerators.telescope()

        preset = EquipmentPreset.objects.create(
            user=user1,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope)

        # Create matching images for both users
        image1 = Generators.image(user=user1)
        image1.imaging_telescopes_2.add(telescope)

        image2 = Generators.image(user=user2)
        image2.imaging_telescopes_2.add(telescope)

        # Filter queryset by user1
        filtered_queryset = Image.objects.filter(user=user1)
        results = EquipmentService.find_images_featuring_preset(preset, filtered_queryset)

        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), image1)

    def test_find_images_featuring_preset_none_queryset(self):
        user = Generators.user()
        telescope = EquipmentGenerators.telescope()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope)

        image = Generators.image(user=user)
        image.imaging_telescopes_2.add(telescope)

        # Test with None queryset
        results = EquipmentService.find_images_featuring_preset(preset, None)
        self.assertGreater(results.count(), 0)
        self.assertIn(image, results)

    def test_find_images_featuring_preset_empty_queryset(self):
        user = Generators.user()
        telescope = EquipmentGenerators.telescope()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope)

        # Use empty queryset
        empty_queryset = Image.objects.none()
        results = EquipmentService.find_images_featuring_preset(preset, empty_queryset)
        self.assertEqual(results.count(), 0)

    def test_find_images_featuring_preset_image_with_additional_equipment(self):
        user = Generators.user()
        # Preset equipment
        telescope1 = EquipmentGenerators.telescope()
        camera1 = EquipmentGenerators.camera()

        # Additional equipment not in preset
        telescope2 = EquipmentGenerators.telescope()
        camera2 = EquipmentGenerators.camera()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope1)
        preset.imaging_cameras.add(camera1)

        # Image with all preset equipment plus extra
        matching_image = Generators.image(user=user)
        matching_image.imaging_telescopes_2.add(telescope1, telescope2)  # Has extra telescope
        matching_image.imaging_cameras_2.add(camera1, camera2)  # Has extra camera

        results = EquipmentService.find_images_featuring_preset(preset, Image.objects.all())
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), matching_image)

    def test_find_images_featuring_preset_multiple_preset_matches(self):
        user = Generators.user()

        # Equipment items
        telescope1 = EquipmentGenerators.telescope()
        telescope2 = EquipmentGenerators.telescope()
        camera1 = EquipmentGenerators.camera()
        camera2 = EquipmentGenerators.camera()

        # First preset with telescope1 and camera1
        preset1 = EquipmentPreset.objects.create(
            user=user,
            name="Preset 1",
        )
        preset1.imaging_telescopes.add(telescope1)
        preset1.imaging_cameras.add(camera1)

        # Second preset with telescope2 and camera2
        preset2 = EquipmentPreset.objects.create(
            user=user,
            name="Preset 2",
        )
        preset2.imaging_telescopes.add(telescope2)
        preset2.imaging_cameras.add(camera2)

        # Image with ALL equipment (should match both presets)
        image = Generators.image(user=user)
        image.imaging_telescopes_2.add(telescope1, telescope2)
        image.imaging_cameras_2.add(camera1, camera2)

        # Test first preset
        results1 = EquipmentService.find_images_featuring_preset(preset1, Image.objects.all())
        self.assertEqual(results1.count(), 1)
        self.assertEqual(results1.first(), image)

        # Test second preset
        results2 = EquipmentService.find_images_featuring_preset(preset2, Image.objects.all())
        self.assertEqual(results2.count(), 1)
        self.assertEqual(results2.first(), image)

    def test_find_images_featuring_preset_subset_matches(self):
        user = Generators.user()

        # Equipment for minimal preset
        telescope = EquipmentGenerators.telescope()

        # Additional equipment for comprehensive preset
        camera = EquipmentGenerators.camera()
        mount = EquipmentGenerators.mount()

        # Minimal preset with just telescope
        minimal_preset = EquipmentPreset.objects.create(
            user=user,
            name="Minimal Preset",
        )
        minimal_preset.imaging_telescopes.add(telescope)

        # Comprehensive preset with all equipment
        comprehensive_preset = EquipmentPreset.objects.create(
            user=user,
            name="Comprehensive Preset",
        )
        comprehensive_preset.imaging_telescopes.add(telescope)
        comprehensive_preset.imaging_cameras.add(camera)
        comprehensive_preset.mounts.add(mount)

        # Image with all equipment
        fully_equipped_image = Generators.image(user=user)
        fully_equipped_image.imaging_telescopes_2.add(telescope)
        fully_equipped_image.imaging_cameras_2.add(camera)
        fully_equipped_image.mounts_2.add(mount)

        # The image should match both presets
        minimal_results = EquipmentService.find_images_featuring_preset(minimal_preset, Image.objects.all())
        self.assertEqual(minimal_results.count(), 1)
        self.assertEqual(minimal_results.first(), fully_equipped_image)

        comprehensive_results = EquipmentService.find_images_featuring_preset(comprehensive_preset, Image.objects.all())
        self.assertEqual(comprehensive_results.count(), 1)
        self.assertEqual(comprehensive_results.first(), fully_equipped_image)
