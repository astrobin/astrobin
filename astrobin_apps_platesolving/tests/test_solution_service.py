from django.core.files import File
from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_platesolving.services import SolutionService
from astrobin_apps_platesolving.tests.platesolving_generators import PlateSolvingGenerators


class SolutionServiceTest(TestCase):
    def test_get_or_create_advanced_settings_only_image(self):
        image = Generators.image()
        advanced_settings, created = SolutionService.get_or_create_advanced_settings(image)
        self.assertIsNone(advanced_settings.sample_raw_frame_file.name)
        self.assertTrue(created)

    def test_get_or_create_advanced_settings_revision_inherits_everything(self):
        image = Generators.image()

        solution = PlateSolvingGenerators.solution(image)
        advanced_settings, created = SolutionService.get_or_create_advanced_settings(image)
        advanced_settings.sample_raw_frame_file = File(open('astrobin/fixtures/test.fits'), "test.fits")
        advanced_settings.scaled_font_size = "L"

        solution.advanced_settings = advanced_settings
        solution.content_object = image
        solution.save()
        advanced_settings.save()

        advanced_settings, created = SolutionService.get_or_create_advanced_settings(
            Generators.imageRevision(image=image))

        self.assertNotEquals(advanced_settings.sample_raw_frame_file.name, "")
        self.assertEquals(advanced_settings.scaled_font_size, "L")
        self.assertFalse(created)

    def test_get_or_create_advanced_settings_image_does_not_inherit_file(self):
        image = Generators.image()

        solution = PlateSolvingGenerators.solution(image)
        advanced_settings, created = SolutionService.get_or_create_advanced_settings(image)
        advanced_settings.sample_raw_frame_file = File(open('astrobin/fixtures/test.fits'), "test.fits")
        advanced_settings.scaled_font_size = "L"

        solution.advanced_settings = advanced_settings
        solution.content_object = image
        solution.save()
        advanced_settings.save()

        advanced_settings, created = SolutionService.get_or_create_advanced_settings(Generators.image(user=image.user))

        self.assertIsNone(advanced_settings.sample_raw_frame_file.name)
        self.assertEquals(advanced_settings.scaled_font_size, "L")
        self.assertFalse(created)
