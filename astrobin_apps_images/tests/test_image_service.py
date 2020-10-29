from django.test import TestCase
from mock import patch

from astrobin.models import Image
from astrobin.tests.generators import Generators
from astrobin_apps_images.services import ImageService
from astrobin_apps_platesolving.tests.platesolving_generators import PlateSolvingGenerators


class TestImageService(TestCase):
    def test_get_revisions_excludes_corrupted(self):
        image = Generators.image(is_wip=True)
        Generators.imageRevision(image=image)
        Generators.imageRevision(image=image, corrupted=True, label='C')

        self.assertEquals(ImageService(image).get_revisions().count(), 1)

    def test_get_revisions_includes_corrupted(self):
        image = Generators.image(is_wip=True)
        Generators.imageRevision(image=image)
        Generators.imageRevision(image=image, corrupted=True, label='C')

        self.assertEquals(ImageService(image).get_revisions(include_corrupted=True).count(), 2)

    def test_get_revisions_with_description(self):
        image = Generators.image(is_wip=True)
        Generators.imageRevision(image=image)
        Generators.imageRevision(image=image, label='C', description='Foo')

        self.assertEquals(ImageService(image).get_revisions_with_description().count(), 1)

    def test_get_next_available_revision_label(self):
        image = Generators.image(is_wip=True)
        Generators.imageRevision(image=image)
        self.assertEquals(ImageService(image).get_next_available_revision_label(), 'C')

    def test_get_next_available_revision_label_after_z(self):
        image = Generators.image(is_wip=True)
        Generators.imageRevision(image=image, label='Z')
        self.assertEquals(ImageService(image).get_next_available_revision_label(), 'BA')

    def test_get_next_available_revision_label_with_corrupted_revision(self):
        image = Generators.image(is_wip=True)
        Generators.imageRevision(image=image)
        Generators.imageRevision(image=image, corrupted=True, label='C')
        self.assertEquals(ImageService(image).get_next_available_revision_label(), 'D')

    def test_get_next_available_revision_label_with_deleted_revision(self):
        image = Generators.image(is_wip=True)
        Generators.imageRevision(image=image)
        to_delete = Generators.imageRevision(image=image, corrupted=True, label='C')
        to_delete.delete()
        self.assertEquals(ImageService(image).get_next_available_revision_label(), 'D')

    def test_get_revision(self):
        image = Generators.image(is_wip=True)
        revision = Generators.imageRevision(image=image)
        self.assertEquals(ImageService(image).get_revision(revision.label), revision)

    def test_get_final_revision_label(self):
        image = Generators.image(is_wip=True)
        revision = Generators.imageRevision(image=image, is_final=True)
        self.assertEquals(ImageService(image).get_final_revision_label(), revision.label)
        another = Generators.imageRevision(image=image, is_final=True, label='C')
        self.assertEquals(ImageService(image).get_final_revision_label(), another.label)

    def test_get_final_revision(self):
        image = Generators.image(is_wip=True)
        final = Generators.imageRevision(image=image, is_final=True)
        Generators.imageRevision(image=image, is_final=False, label='C')
        self.assertEquals(ImageService(image).get_final_revision(), final)

    def test_get_default_cropping(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        self.assertEquals(ImageService(image).get_default_cropping(), '0,0,1000,1000')

    @patch.object(ImageService, 'get_revision')
    def test_get_default_cropping_revision(self, get_revision):
        image = Generators.image(is_wip=True)
        revision = Generators.imageRevision(image=image)
        revision.w = revision.h = 1000
        get_revision.return_value = revision
        self.assertEquals(ImageService(image).get_default_cropping(revision_label=revision.label), '0,0,1000,1000')

    def test_get_default_cropping_rectangular(self):
        image = Generators.image(is_wip=True)
        image.w = 1000
        image.h = 600
        self.assertEquals(ImageService(image).get_default_cropping(), '200,0,800,600')

    def test_get_crop_box_gallery(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,100,200,200'
        self.assertEquals(ImageService(image).get_crop_box('gallery'), '100,100,200,200')

    def test_get_crop_box_gallery_large_crop(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,100,900,900'
        self.assertEquals(ImageService(image).get_crop_box('gallery'), '100,100,900,900')

    def test_get_crop_box_gallery_inverted(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,100,200,200'
        self.assertEquals(ImageService(image).get_crop_box('gallery_inverted'), '100,100,200,200')

    def test_get_crop_box_collection(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,100,200,200'
        self.assertEquals(ImageService(image).get_crop_box('collection'), '100,100,200,200')

    def test_get_crop_box_iotd_top_left(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,100,200,200'
        self.assertEquals(ImageService(image).get_crop_box('iotd'), '0,0,1000,380')

    def test_get_crop_box_iotd_bottom_left(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,800,200,900'
        self.assertEquals(ImageService(image).get_crop_box('iotd'), '0,620,1000,1000')

    def test_get_crop_box_iotd_top_right(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '800,100,900,200'
        self.assertEquals(ImageService(image).get_crop_box('iotd'), '0,0,1000,380')

    def test_get_crop_box_iotd_bottom_right(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '800,800,900,900'
        self.assertEquals(ImageService(image).get_crop_box('iotd'), '0,620,1000,1000')

    def test_get_crop_box_iotd_center(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '450,450,550,550'
        self.assertEquals(ImageService(image).get_crop_box('iotd'), '0,310,1000,690')

    def test_get_crop_box_iotd_center_large_crop(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '10,10,990,990'
        self.assertEquals(ImageService(image).get_crop_box('iotd'), '0,310,1000,690')

    def test_get_crop_box_iotd_center_example_1(self):
        image = Generators.image(is_wip=True)
        image.w = 400
        image.h = 800
        image.square_cropping = '50,50,350,350'
        self.assertEquals(ImageService(image).get_crop_box('iotd'), '0,124,400,276')

    def test_get_crop_box_iotd_center_example_2(self):
        image = Generators.image(is_wip=True)
        image.w = 2100
        image.h = 2500
        image.square_cropping = '100,400,100,2200'
        self.assertEquals(ImageService(image).get_crop_box('iotd'), '0,901,2100,1699')

    def test_get_crop_box_iotd_edge(self):
        image = Generators.image(is_wip=True)
        image.w = 1200
        image.h = 500
        image.square_cropping = '0,20,0,20'
        self.assertEquals(ImageService(image).get_crop_box('iotd'), '0,0,1200,455')

    def test_get_crop_box_iotd_tiny_image(self):
        image = Generators.image(is_wip=True)
        image.w = 100
        image.h = 100
        image.square_cropping = '0,0,50,50'
        self.assertEquals(ImageService(image).get_crop_box('iotd'), '0,6,100,44')

    def test_get_crop_box_regular(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '450,450,550,550'
        self.assertEquals(ImageService(image).get_crop_box('regular'), None)

    def test_get_hemisphere_no_solution(self):
        image = Generators.image()
        PlateSolvingGenerators.solution(image)

        self.assertEquals(Image.HEMISPHERE_TYPE_UNKNOWN, ImageService(image).get_hemisphere())

    def test_get_hemisphere_no_declination(self):
        image = Generators.image()
        solution = PlateSolvingGenerators.solution(image)

        solution.dec = None
        solution.save()

        self.assertEquals(Image.HEMISPHERE_TYPE_UNKNOWN, ImageService(image).get_hemisphere())

    def test_get_hemisphere_zero_declination(self):
        image = Generators.image()
        solution = PlateSolvingGenerators.solution(image)

        solution.dec = 0
        solution.save()

        self.assertEquals(Image.HEMISPHERE_TYPE_NORTHERN, ImageService(image).get_hemisphere())

    def test_get_hemisphere_positive_declination(self):
        image = Generators.image()
        solution = PlateSolvingGenerators.solution(image)

        solution.dec = 1
        solution.save()

        self.assertEquals(Image.HEMISPHERE_TYPE_NORTHERN, ImageService(image).get_hemisphere())

    def test_get_hemisphere_negative_declination(self):
        image = Generators.image()
        solution = PlateSolvingGenerators.solution(image)

        solution.dec = -1
        solution.save()

        self.assertEquals(Image.HEMISPHERE_TYPE_SOUTHERN, ImageService(image).get_hemisphere())

    def test_get_hemisphere_positive_declination_revision(self):
        image = Generators.image()
        image_solution = PlateSolvingGenerators.solution(image)

        revision = Generators.imageRevision(image=image)
        revision_solution = PlateSolvingGenerators.solution(revision)

        image_solution.dec = 1
        image_solution.save()

        revision_solution.dec = -1
        revision_solution.save()

        self.assertEquals(Image.HEMISPHERE_TYPE_NORTHERN, ImageService(image).get_hemisphere())
        self.assertEquals(Image.HEMISPHERE_TYPE_SOUTHERN, ImageService(image).get_hemisphere(revision.label))
