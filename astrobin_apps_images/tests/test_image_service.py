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

    def test_get_revisions_excludes_corrupted(self):
        image = Generators.image()
        Generators.imageRevision(image=image)
        Generators.imageRevision(image=image, corrupted=True, label='C')

        self.assertEquals(ImageService(image).get_revisions().count(), 1)

    def test_get_revisions_includes_corrupted(self):
        image = Generators.image()
        Generators.imageRevision(image=image)
        Generators.imageRevision(image=image, corrupted=True, label='C')

        self.assertEquals(ImageService(image).get_revisions(include_corrupted=True).count(), 2)

    def test_get_revisions_with_description(self):
        image = Generators.image()
        Generators.imageRevision(image=image)
        Generators.imageRevision(image=image, label='C', description='Foo')

        self.assertEquals(ImageService(image).get_revisions_with_description().count(), 1)
