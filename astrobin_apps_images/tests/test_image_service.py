from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_images.services import ImageService


class TestImageService(TestCase):
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
