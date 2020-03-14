from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_images.services import ImageService


class TestImageService(TestCase):
    def test_is_corrupted(self):
        image = Generators.image()
        corrupted = Generators.image(corrupted=True)

        self.assertFalse(ImageService(image).is_corrupted())
        self.assertTrue(ImageService(corrupted).is_corrupted())

    def test_is_corrupted_when_final_revision_is(self):
        image = Generators.image(is_final=False)
        Generators.imageRevision(image=image, corrupted=True, is_final=True)

        self.assertTrue(ImageService(image).is_corrupted())

    def test_is_not_corrupted_when_non_final_revision_is(self):
        image = Generators.image(is_final=False)
        Generators.imageRevision(image=image, corrupted=True, is_final=False)
        Generators.imageRevision(image=image, is_final=True, label='C')

        self.assertFalse(ImageService(image).is_corrupted())
