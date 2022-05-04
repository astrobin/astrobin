from django.test import TestCase

from astrobin.services.gear_service import GearService
from astrobin.tests.generators import Generators


class GearServiceTest(TestCase):
    def test_has_legacy_gear_false(self):
        image = Generators.image()

        self.assertFalse(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_imaging_telescopes(self):
        image = Generators.image()
        gear_item = Generators.telescope()
        image.imaging_telescopes.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_guiding_telescopes(self):
        image = Generators.image()
        gear_item = Generators.telescope()
        image.guiding_telescopes.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_mounts(self):
        image = Generators.image()
        gear_item = Generators.mount()
        image.mounts.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_imaging_cameras(self):
        image = Generators.image()
        gear_item = Generators.camera()
        image.imaging_cameras.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_guiding_cameras(self):
        image = Generators.image()
        gear_item = Generators.camera()
        image.guiding_cameras.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_focal_reducers(self):
        image = Generators.image()
        gear_item = Generators.focal_reducer()
        image.focal_reducers.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_software(self):
        image = Generators.image()
        gear_item = Generators.software()
        image.software.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_filters(self):
        image = Generators.image()
        gear_item = Generators.filter()
        image.filters.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_accessories(self):
        image = Generators.image()
        gear_item = Generators.accessory()
        image.accessories.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))
