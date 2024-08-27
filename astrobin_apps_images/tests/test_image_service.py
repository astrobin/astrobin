from actstream.models import Action
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from mock import patch

from astrobin.enums import SubjectType
from astrobin.enums.display_image_download_menu import DownloadLimitation
from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Image, ImageRevision
from astrobin.tests.generators import Generators
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from astrobin_apps_images.services import ImageService
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.tests.platesolving_generators import PlateSolvingGenerators


class TestImageService(TestCase):
    def test_get_revisions_with_title_or_description_only_description(self):
        image = Generators.image(is_wip=True)
        Generators.image_revision(image=image)
        Generators.image_revision(image=image, label='C', description='Foo')

        self.assertEqual(ImageService(image).get_revisions_with_title_or_description().count(), 1)

    def test_get_revisions_with_title_or_description_only_title(self):
        image = Generators.image(is_wip=True)
        Generators.image_revision(image=image)
        Generators.image_revision(image=image, label='C', title='Foo')

        self.assertEqual(ImageService(image).get_revisions_with_title_or_description().count(), 1)

    def test_get_revisions_with_title_or_description_only_title_but_empty(self):
        image = Generators.image(is_wip=True)
        Generators.image_revision(image=image)
        Generators.image_revision(image=image, label='C', title='')

        self.assertEqual(ImageService(image).get_revisions_with_title_or_description().count(), 0)

    def test_get_revisions_with_title_or_description(self):
        image = Generators.image(is_wip=True)
        Generators.image_revision(image=image)
        Generators.image_revision(image=image, label='C', title='Foo', description='Bar')

        self.assertEqual(ImageService(image).get_revisions_with_title_or_description().count(), 1)

    def test_get_next_available_revision_label(self):
        image = Generators.image(is_wip=True)
        Generators.image_revision(image=image)
        self.assertEqual(ImageService(image).get_next_available_revision_label(), 'C')

    def test_get_next_available_revision_label_after_z(self):
        image = Generators.image(is_wip=True)
        Generators.image_revision(image=image, label='Z')
        self.assertEqual(ImageService(image).get_next_available_revision_label(), 'BA')

    def test_get_next_available_revision_label_with_deleted_revision(self):
        image = Generators.image(is_wip=True)
        Generators.image_revision(image=image)
        to_delete = Generators.image_revision(image=image, label='C')
        to_delete.delete()
        self.assertEqual(ImageService(image).get_next_available_revision_label(), 'D')

    def test_get_revision(self):
        image = Generators.image(is_wip=True)
        revision = Generators.image_revision(image=image)
        self.assertEqual(ImageService(image).get_revision(revision.label), revision)

    def test_get_final_revision_label(self):
        image = Generators.image(is_wip=True)
        revision = Generators.image_revision(image=image, is_final=True)
        self.assertEqual(ImageService(image).get_final_revision_label(), revision.label)
        another = Generators.image_revision(image=image, is_final=True, label='C')
        self.assertEqual(ImageService(image).get_final_revision_label(), another.label)

    def test_get_final_revision(self):
        image = Generators.image(is_wip=True)
        final = Generators.image_revision(image=image, is_final=True)
        Generators.image_revision(image=image, is_final=False, label='C')
        self.assertEqual(ImageService(image).get_final_revision(), final)

    def test_get_default_cropping(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        self.assertEqual(ImageService(image).get_default_cropping(), '0,0,1000,1000')

    @patch.object(ImageService, 'get_revision')
    def test_get_default_cropping_revision(self, get_revision):
        image = Generators.image(is_wip=True)
        revision = Generators.image_revision(image=image)
        revision.w = revision.h = 1000
        get_revision.return_value = revision
        self.assertEqual(ImageService(image).get_default_cropping(revision_label=revision.label), '0,0,1000,1000')

    def test_get_default_cropping_rectangular(self):
        image = Generators.image(is_wip=True)
        image.w = 1000
        image.h = 600
        self.assertEqual(ImageService(image).get_default_cropping(), '200,0,800,600')

    def test_get_crop_box_gallery(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,100,200,200'
        self.assertEqual(ImageService(image).get_crop_box('gallery'), '100,100,200,200')

    def test_get_crop_box_gallery_large_crop(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,100,900,900'
        self.assertEqual(ImageService(image).get_crop_box('gallery'), '100,100,900,900')

    def test_get_crop_box_gallery_inverted(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,100,200,200'
        self.assertEqual(ImageService(image).get_crop_box('gallery_inverted'), '100,100,200,200')

    def test_get_crop_box_collection(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,100,200,200'
        self.assertEqual(ImageService(image).get_crop_box('collection'), '100,100,200,200')

    def test_get_crop_box_iotd_top_left(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,100,200,200'
        self.assertEqual(ImageService(image).get_crop_box('iotd'), '0,0,1000,380')

    def test_get_crop_box_iotd_bottom_left(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '100,800,200,900'
        self.assertEqual(ImageService(image).get_crop_box('iotd'), '0,620,1000,1000')

    def test_get_crop_box_iotd_top_right(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '800,100,900,200'
        self.assertEqual(ImageService(image).get_crop_box('iotd'), '0,0,1000,380')

    def test_get_crop_box_iotd_bottom_right(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '800,800,900,900'
        self.assertEqual(ImageService(image).get_crop_box('iotd'), '0,620,1000,1000')

    def test_get_crop_box_iotd_center(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '450,450,550,550'
        self.assertEqual(ImageService(image).get_crop_box('iotd'), '0,310,1000,690')

    def test_get_crop_box_iotd_center_large_crop(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '10,10,990,990'
        self.assertEqual(ImageService(image).get_crop_box('iotd'), '0,310,1000,690')

    def test_get_crop_box_iotd_center_example_1(self):
        image = Generators.image(is_wip=True)
        image.w = 400
        image.h = 800
        image.square_cropping = '50,50,350,350'
        self.assertEqual(ImageService(image).get_crop_box('iotd'), '0,124,400,276')

    def test_get_crop_box_iotd_center_example_2(self):
        image = Generators.image(is_wip=True)
        image.w = 2100
        image.h = 2500
        image.square_cropping = '100,400,100,2200'
        self.assertEqual(ImageService(image).get_crop_box('iotd'), '0,901,2100,1699')

    def test_get_crop_box_iotd_edge(self):
        image = Generators.image(is_wip=True)
        image.w = 1200
        image.h = 500
        image.square_cropping = '0,20,0,20'
        self.assertEqual(ImageService(image).get_crop_box('iotd'), '0,0,1200,455')

    def test_get_crop_box_iotd_tiny_image(self):
        image = Generators.image(is_wip=True)
        image.w = 100
        image.h = 100
        image.square_cropping = '0,0,50,50'
        self.assertEqual(ImageService(image).get_crop_box('iotd'), '0,6,100,44')

    def test_get_crop_box_regular(self):
        image = Generators.image(is_wip=True)
        image.w = image.h = 1000
        image.square_cropping = '450,450,550,550'
        self.assertEqual(ImageService(image).get_crop_box('regular'), None)

    def test_get_hemisphere_no_solution(self):
        image = Generators.image()
        PlateSolvingGenerators.solution(image)

        self.assertEqual(Image.HEMISPHERE_TYPE_UNKNOWN, ImageService(image).get_hemisphere())

    def test_get_hemisphere_no_revision(self):
        image = Generators.image()
        solution = PlateSolvingGenerators.solution(image)

        solution.dec = 0
        solution.save()

        self.assertEqual(Image.HEMISPHERE_TYPE_UNKNOWN, ImageService(image).get_hemisphere('z'))


    def test_get_hemisphere_no_declination(self):
        image = Generators.image()
        solution = PlateSolvingGenerators.solution(image)

        solution.dec = None
        solution.save()

        self.assertEqual(Image.HEMISPHERE_TYPE_UNKNOWN, ImageService(image).get_hemisphere())

    def test_get_hemisphere_zero_declination(self):
        image = Generators.image()
        solution = PlateSolvingGenerators.solution(image)

        solution.dec = 0
        solution.save()

        self.assertEqual(Image.HEMISPHERE_TYPE_NORTHERN, ImageService(image).get_hemisphere())

    def test_get_hemisphere_positive_declination(self):
        image = Generators.image()
        solution = PlateSolvingGenerators.solution(image)

        solution.dec = 1
        solution.save()

        self.assertEqual(Image.HEMISPHERE_TYPE_NORTHERN, ImageService(image).get_hemisphere())

    def test_get_hemisphere_negative_declination(self):
        image = Generators.image()
        solution = PlateSolvingGenerators.solution(image)

        solution.dec = -1
        solution.save()

        self.assertEqual(Image.HEMISPHERE_TYPE_SOUTHERN, ImageService(image).get_hemisphere())

    def test_get_hemisphere_positive_declination_revision(self):
        image = Generators.image()
        image_solution = PlateSolvingGenerators.solution(image)

        revision = Generators.image_revision(image=image)
        revision_solution = PlateSolvingGenerators.solution(revision)

        image_solution.dec = 1
        image_solution.save()

        revision_solution.dec = -1
        revision_solution.save()

        self.assertEqual(Image.HEMISPHERE_TYPE_NORTHERN, ImageService(image).get_hemisphere())
        self.assertEqual(Image.HEMISPHERE_TYPE_SOUTHERN, ImageService(image).get_hemisphere(revision.label))

    def test_delete_original_when_no_revisions(self):
        image= Generators.image()
        PlateSolvingGenerators.solution(image)

        self.assertEqual(1, Image.objects.all().count())
        self.assertEqual(1, Solution.objects.all().count())

        ImageService(image).delete_original()

        self.assertEqual(0, Image.objects.all().count())
        self.assertEqual(0, Solution.objects.all().count())

    def test_delete_original_preserves_title_and_description(self):
        image = Generators.image(image_file='original.jpg', title='Foo', description='Foo')
        Generators.image_revision(image=image, image_file='revision.jpg', title='Bar', description='Bar')

        ImageService(image).delete_original()

        image = Image.objects.get(pk=image.pk)
        self.assertEqual('revision.jpg', image.image_file)
        self.assertEqual('Foo (Bar)', image.title)
        self.assertEqual('Foo\nBar', image.description)
        self.assertEqual(1, Image.objects.all().count())

    def test_delete_original_preserves_square_cropping(self):
        image = Generators.image(image_file='original.jpg')
        Image.objects.filter(pk=image.pk).update(square_cropping='0,0,100,100')
        revision = Generators.image_revision(image=image, image_file='revision.jpg')
        ImageRevision.objects.filter(pk=revision.pk).update(square_cropping='50,50,150,150')

        ImageService(image).delete_original()

        image = Image.objects.get(pk=image.pk)
        self.assertEqual('revision.jpg', image.image_file)
        self.assertEqual(image.square_cropping, '50,50,150,150')
        self.assertEqual(1, Image.objects.all().count())

    def test_delete_original_for_videos(self):
        image = Generators.image(video_file='original.mov')
        revision = Generators.image_revision(image=image, video_file='revision.mov')

        ImageService(image).delete_original()

        image = Image.objects.get(pk=image.pk)
        self.assertEqual(revision.video_file, image.video_file)
        self.assertEqual(1, Image.objects.all().count())

    def test_delete_original_when_new_title_is_too_long(self):
        original_title = Generators.random_string(128)
        revision_title = Generators.random_string(10)
        image = Generators.image(image_file='original.jpg', title=original_title)
        Generators.image_revision(image=image, image_file='revision.jpg', title=revision_title)

        ImageService(image).delete_original()

        image = Image.objects.get(pk=image.pk)
        self.assertEqual('revision.jpg', image.image_file)
        self.assertEqual(f'{original_title[:112]}... ({revision_title})', image.title)

    def test_delete_original_preserves_title_and_description_when_original_has_none(self):
        image = Generators.image(image_file='original.jpg', title='Foo')
        revision = Generators.image_revision(image=image, image_file='revision.jpg', title='Bar', description='Bar')

        ImageService(image).delete_original()

        image = Image.objects.get(pk=image.pk)
        self.assertEqual('revision.jpg', image.image_file)
        self.assertEqual('Foo (Bar)', image.title)
        self.assertEqual('Bar', image.description)
        self.assertEqual(1, Image.objects.all().count())

    def test_delete_original_preserves_title_and_description_when_deleted_revision_has_none(self):
        image = Generators.image(image_file='original.jpg', title='Foo')
        revision = Generators.image_revision(image=image, image_file='revision.jpg')

        ImageService(image).delete_original()

        image = Image.objects.get(pk=image.pk)
        self.assertEqual('revision.jpg', image.image_file)
        self.assertEqual('Foo', image.title)
        self.assertEqual(None, image.description)
        self.assertEqual(1, Image.objects.all().count())

    def test_delete_original_when_one_revision_and_original_is_final(self):
        image = Generators.image(image_file='original.jpg')
        PlateSolvingGenerators.solution(image, image_file='original_solution.jpg')

        revision = Generators.image_revision(image=image, image_file='revision.jpg')
        revision_solution = PlateSolvingGenerators.solution(revision, image_file='revision_solution.jpg')

        ImageService(image).delete_original()

        self.assertEqual('revision.jpg', image.image_file)
        self.assertTrue(image.is_final)
        self.assertEqual('revision_solution.jpg', revision_solution.image_file)
        self.assertEqual(image.pk, revision_solution.object_id)
        self.assertEqual(1, Image.objects.all().count())
        self.assertEqual(1, Solution.objects.all().count())

    def test_delete_original_when_one_revision_and_revision_is_final(self):
        image = Generators.image(image_file='original.jpg', is_final=False)
        Generators.image_revision(image=image, image_file='revision.jpg', is_final=True)

        ImageService(image).delete_original()

        image = Image.objects.get(pk=image.pk)

        self.assertEqual('revision.jpg', image.image_file)
        self.assertTrue(image.is_final)

    def test_delete_original_when_two_revisions_and_original_is_final(self):
        image = Generators.image(image_file='original.jpg', is_final=True)
        Generators.image_revision(image=image, image_file='revision_b.jpg', is_final=False, label='B')
        Generators.image_revision(image=image, image_file='revision_c.jpg', is_final=False, label='C')

        ImageService(image).delete_original()

        self.assertEqual('revision_b.jpg', image.image_file)
        self.assertTrue(image.is_final)
        self.assertEqual(1, ImageService(image).get_revisions().count())
        self.assertEqual('C', ImageService(image).get_revisions().first().label)


    def test_delete_original_when_two_revisions_and_B_is_final(self):
        image = Generators.image(image_file='original.jpg', is_final=False)
        Generators.image_revision(image=image, image_file='revision_b.jpg', is_final=True, label='B')
        Generators.image_revision(image=image, image_file='revision_c.jpg', is_final=False, label='C')

        ImageService(image).delete_original()

        self.assertEqual('revision_b.jpg', image.image_file)
        self.assertTrue(image.is_final)
        self.assertEqual(1, ImageService(image).get_revisions().count())
        self.assertEqual('C', ImageService(image).get_revisions().first().label)

    def test_delete_original_when_two_revisions_and_C_is_final(self):
        image = Generators.image(image_file='original.jpg', is_final=False)
        Generators.image_revision(image=image, image_file='revision_b.jpg', is_final=False, label='B')
        Generators.image_revision(image=image, image_file='revision_c.jpg', is_final=True, label='C')

        ImageService(image).delete_original()

        image.refresh_from_db()

        self.assertEqual('revision_b.jpg', image.image_file)
        self.assertFalse(image.is_final)
        self.assertEqual(1, ImageService(image).get_revisions().count())
        self.assertEqual('C', ImageService(image).get_revisions().first().label)
        self.assertTrue(ImageService(image).get_revisions().first().is_final)

    def test_delete_original_preserves_mouse_hover_settings(self):
        image = Generators.image(image_file='original.jpg', is_final=False)
        b = Generators.image_revision(image=image, image_file='revision_b.jpg', is_final=False, label='B')
        c = Generators.image_revision(image=image, image_file='revision_c.jpg', is_final=True, label='C')

        ImageRevision.objects.filter(id=b.id).update(mouse_hover_image=f'REVISION__{c.label}')

        ImageService(image).delete_original()

        self.assertEqual('revision_b.jpg', image.image_file)
        self.assertEqual(f'REVISION__{c.label}', image.mouse_hover_image)
        self.assertFalse(image.is_final)
        self.assertEqual(1, ImageService(image).get_revisions().count())
        self.assertEqual('C', ImageService(image).get_revisions().first().label)

    @patch.object(ImageService, 'is_platesolvable')
    def test_needs_premium_subscription_to_platesolve_solar_system(self, is_platesolvable):
        image = Generators.image()

        is_platesolvable.return_value = False

        self.assertFalse(ImageService(image).needs_premium_subscription_to_platesolve())

    @patch.object(ImageService, 'is_platesolvable')
    @patch.object(ImageService, 'is_platesolving_attempted')
    def test_needs_premium_subscription_to_platesolve_solving_already_attempted(
            self, is_platesolving_attempted, is_platesolvable):
        image = Generators.image()

        is_platesolving_attempted.return_value = True
        is_platesolvable.return_value = True

        self.assertFalse(ImageService(image).needs_premium_subscription_to_platesolve())

    @patch.object(ImageService, 'is_platesolvable')
    @patch.object(ImageService, 'is_platesolving_attempted')
    @patch('astrobin_apps_images.services.image_service.is_free')
    def test_needs_premium_subscription_to_platesolve_solving_already_attempted(
            self, is_free, is_platesolving_attempted, is_platesolvable):
        image = Generators.image()
        image.subject_type = SubjectType.DEEP_SKY
        image.save()

        is_free.return_value = False
        is_platesolving_attempted.return_value = False
        is_platesolvable.return_value = True

        self.assertFalse(ImageService(image).needs_premium_subscription_to_platesolve())

    def test_display_download_menu_me_only(self):
        image = Generators.image(download_limitations=DownloadLimitation.ME_ONLY)
        self.assertTrue(ImageService(image).display_download_menu(image.user))
        self.assertFalse(ImageService(image).display_download_menu(Generators.user()))
        self.assertFalse(ImageService(image).display_download_menu(AnonymousUser))

    def test_display_download_menu_me_only_but_superuser(self):
        image = Generators.image(download_limitations=DownloadLimitation.ME_ONLY)
        superuser = User.objects.create_superuser('superuser', 'superuser@test.com', 'password')
        self.assertTrue(ImageService(image).display_download_menu(superuser))

    def test_display_download_menu_null(self):
        image = Generators.image(download_limitations=None)
        self.assertTrue(ImageService(image).display_download_menu(image.user))
        self.assertFalse(ImageService(image).display_download_menu(Generators.user()))
        self.assertFalse(ImageService(image).display_download_menu(AnonymousUser))

    def test_display_download_menu_everybody(self):
        image = Generators.image(download_limitations=DownloadLimitation.EVERYBODY)
        self.assertTrue(ImageService(image).display_download_menu(image.user))
        self.assertTrue(ImageService(image).display_download_menu(Generators.user()))
        self.assertTrue(ImageService(image).display_download_menu(AnonymousUser))

    def test_get_equipment_list_when_empty(self):
        image = Generators.image()

        equipment_list = ImageService(image).get_equipment_list()

        self.assertEqual(0, len(equipment_list['imaging_telescopes']))
        self.assertEqual(0, len(equipment_list['imaging_cameras']))
        self.assertEqual(0, len(equipment_list['mounts']))
        self.assertEqual(0, len(equipment_list['filters']))
        self.assertEqual(0, len(equipment_list['accessories']))
        self.assertEqual(0, len(equipment_list['software']))
        self.assertEqual(0, len(equipment_list['guiding_telescopes']))
        self.assertEqual(0, len(equipment_list['guiding_cameras']))

    def test_get_equipment_list_when_only_legacy_gear(self):
        image = Generators.image()

        image.imaging_telescopes.add(Generators.telescope(make='My make', name='My imaging telescope'))
        image.imaging_cameras.add(Generators.camera(make='My make', name='My imaging camera'))
        image.mounts.add(Generators.mount(make='My make', name='My mount'))
        image.filters.add(Generators.filter(make='My make', name='My filter'))
        image.accessories.add(Generators.accessory(make='My make', name='My accessory'))
        image.focal_reducers.add(Generators.focal_reducer(make='My make', name='My focal reducer'))
        image.software.add(Generators.software(make='My make', name='My software'))
        image.guiding_telescopes.add(Generators.telescope(make='My make', name='My guiding telescope'))
        image.guiding_cameras.add(Generators.camera(make='My make', name='My guiding camera'))

        equipment_list = ImageService(image).get_equipment_list()

        self.assertEqual(1, len(equipment_list['imaging_telescopes']))
        self.assertEqual(1, len(equipment_list['imaging_cameras']))
        self.assertEqual(1, len(equipment_list['mounts']))
        self.assertEqual(1, len(equipment_list['filters']))
        self.assertEqual(2, len(equipment_list['accessories']))
        self.assertEqual(1, len(equipment_list['software']))
        self.assertEqual(1, len(equipment_list['guiding_telescopes']))
        self.assertEqual(1, len(equipment_list['guiding_cameras']))

        self.assertTrue('id' in equipment_list['imaging_telescopes'][0])
        self.assertEqual('My make My imaging telescope', equipment_list['imaging_telescopes'][0]['label'])
        self.assertEqual('LEGACY', equipment_list['imaging_telescopes'][0]['version'])

        self.assertTrue('id' in equipment_list['imaging_cameras'][0])
        self.assertEqual('My make My imaging camera', equipment_list['imaging_cameras'][0]['label'])
        self.assertEqual('LEGACY', equipment_list['imaging_cameras'][0]['version'])

        self.assertTrue('id' in equipment_list['mounts'][0])
        self.assertEqual('My make My mount', equipment_list['mounts'][0]['label'])
        self.assertEqual('LEGACY', equipment_list['mounts'][0]['version'])

        self.assertTrue('id' in equipment_list['filters'][0])
        self.assertEqual('My make My filter', equipment_list['filters'][0]['label'])
        self.assertEqual('LEGACY', equipment_list['filters'][0]['version'])

        self.assertTrue('id' in equipment_list['accessories'][0])
        self.assertEqual('My make My accessory', equipment_list['accessories'][0]['label'])
        self.assertEqual('LEGACY', equipment_list['accessories'][0]['version'])

        self.assertTrue('id' in equipment_list['accessories'][1])
        self.assertEqual('My make My focal reducer', equipment_list['accessories'][1]['label'])
        self.assertEqual('LEGACY', equipment_list['accessories'][0]['version'])

        self.assertTrue('id' in equipment_list['software'][0])
        self.assertEqual('My make My software', equipment_list['software'][0]['label'])
        self.assertEqual('LEGACY', equipment_list['software'][0]['version'])

        self.assertTrue('id' in equipment_list['guiding_telescopes'][0])
        self.assertEqual('My make My guiding telescope', equipment_list['guiding_telescopes'][0]['label'])
        self.assertEqual('LEGACY', equipment_list['guiding_telescopes'][0]['version'])

        self.assertTrue('id' in equipment_list['guiding_cameras'][0])
        self.assertEqual('My make My guiding camera', equipment_list['guiding_cameras'][0]['label'])
        self.assertEqual('LEGACY', equipment_list['guiding_cameras'][0]['version'])

    def test_get_equipment_list_when_only_new_equipment(self):
        image = Generators.image()

        brand = EquipmentGenerators.brand(name='My brand')

        image.imaging_telescopes_2.add(EquipmentGenerators.telescope(brand=brand, name='My new imaging telescope'))
        image.imaging_cameras_2.add(EquipmentGenerators.camera(brand=brand, name='My new imaging camera'))
        image.mounts_2.add(EquipmentGenerators.mount(brand=brand, name='My new mount'))
        image.filters_2.add(EquipmentGenerators.filter(brand=brand, name='My new filter'))
        image.accessories_2.add(EquipmentGenerators.accessory(brand=brand, name='My new accessory'))
        image.software_2.add(EquipmentGenerators.software(brand=brand, name='My new software'))
        image.guiding_telescopes_2.add(EquipmentGenerators.telescope(brand=brand, name='My new guiding telescope'))
        image.guiding_cameras_2.add(EquipmentGenerators.camera(brand=brand, name='My new guiding camera'))

        equipment_list = ImageService(image).get_equipment_list()

        self.assertEqual(1, len(equipment_list['imaging_telescopes']))
        self.assertEqual(1, len(equipment_list['imaging_cameras']))
        self.assertEqual(1, len(equipment_list['mounts']))
        self.assertEqual(1, len(equipment_list['filters']))
        self.assertEqual(1, len(equipment_list['accessories']))
        self.assertEqual(1, len(equipment_list['software']))
        self.assertEqual(1, len(equipment_list['guiding_telescopes']))
        self.assertEqual(1, len(equipment_list['guiding_cameras']))

        self.assertTrue('id' in equipment_list['imaging_telescopes'][0])
        self.assertEqual('My brand My new imaging telescope', equipment_list['imaging_telescopes'][0]['label'])
        self.assertEqual('NEW', equipment_list['imaging_telescopes'][0]['version'])

        self.assertTrue('id' in equipment_list['imaging_cameras'][0])
        self.assertEqual('My brand My new imaging camera', equipment_list['imaging_cameras'][0]['label'])
        self.assertEqual('NEW', equipment_list['imaging_cameras'][0]['version'])

        self.assertTrue('id' in equipment_list['mounts'][0])
        self.assertEqual('My brand My new mount', equipment_list['mounts'][0]['label'])
        self.assertEqual('NEW', equipment_list['mounts'][0]['version'])

        self.assertTrue('id' in equipment_list['filters'][0])
        self.assertEqual('My brand My new filter', equipment_list['filters'][0]['label'])
        self.assertEqual('NEW', equipment_list['filters'][0]['version'])

        self.assertTrue('id' in equipment_list['accessories'][0])
        self.assertEqual('My brand My new accessory', equipment_list['accessories'][0]['label'])
        self.assertEqual('NEW', equipment_list['accessories'][0]['version'])

        self.assertTrue('id' in equipment_list['software'][0])
        self.assertEqual('My brand My new software', equipment_list['software'][0]['label'])
        self.assertEqual('NEW', equipment_list['software'][0]['version'])

        self.assertTrue('id' in equipment_list['guiding_telescopes'][0])
        self.assertEqual('My brand My new guiding telescope', equipment_list['guiding_telescopes'][0]['label'])
        self.assertEqual('NEW', equipment_list['guiding_telescopes'][0]['version'])

        self.assertTrue('id' in equipment_list['guiding_cameras'][0])
        self.assertEqual('My brand My new guiding camera', equipment_list['guiding_cameras'][0]['label'])
        self.assertEqual('NEW', equipment_list['guiding_cameras'][0]['version'])

    def test_get_equipment_list_when_mix(self):
        image = Generators.image()

        image.imaging_telescopes.add(Generators.telescope(make='My make', name='My imaging telescope'))
        image.imaging_cameras.add(Generators.camera(make='My make', name='My imaging camera'))
        image.mounts.add(Generators.mount(make='My make', name='My mount'))
        image.filters.add(Generators.filter(make='My make', name='My filter'))
        image.accessories.add(Generators.accessory(make='My make', name='My accessory'))
        image.focal_reducers.add(Generators.focal_reducer(make='My make', name='My focal reducer'))
        image.software.add(Generators.software(make='My make', name='My software'))
        image.guiding_telescopes.add(Generators.telescope(make='My make', name='My guiding telescope'))
        image.guiding_cameras.add(Generators.camera(make='My make', name='My guiding camera'))

        brand = EquipmentGenerators.brand(name='My brand')

        image.imaging_telescopes_2.add(EquipmentGenerators.telescope(brand=brand, name='My new imaging telescope'))
        image.imaging_cameras_2.add(EquipmentGenerators.camera(brand=brand, name='My new imaging camera'))
        image.mounts_2.add(EquipmentGenerators.mount(brand=brand, name='My new mount'))
        image.filters_2.add(EquipmentGenerators.filter(brand=brand, name='My new filter'))
        image.accessories_2.add(EquipmentGenerators.accessory(brand=brand, name='My new accessory'))
        image.software_2.add(EquipmentGenerators.software(brand=brand, name='My new software'))
        image.guiding_telescopes_2.add(EquipmentGenerators.telescope(brand=brand, name='My new guiding telescope'))
        image.guiding_cameras_2.add(EquipmentGenerators.camera(brand=brand, name='My new guiding camera'))

        equipment_list = ImageService(image).get_equipment_list()

        self.assertEqual(2, len(equipment_list['imaging_telescopes']))
        self.assertEqual(2, len(equipment_list['imaging_cameras']))
        self.assertEqual(2, len(equipment_list['mounts']))
        self.assertEqual(2, len(equipment_list['filters']))
        self.assertEqual(3, len(equipment_list['accessories']))
        self.assertEqual(2, len(equipment_list['software']))
        self.assertEqual(2, len(equipment_list['guiding_telescopes']))
        self.assertEqual(2, len(equipment_list['guiding_cameras']))

        self.assertTrue('id' in equipment_list['imaging_telescopes'][0])
        self.assertEqual('My brand My new imaging telescope', equipment_list['imaging_telescopes'][0]['label'])
        self.assertEqual('NEW', equipment_list['imaging_telescopes'][0]['version'])

        self.assertTrue('id' in equipment_list['imaging_cameras'][0])
        self.assertEqual('My brand My new imaging camera', equipment_list['imaging_cameras'][0]['label'])
        self.assertEqual('NEW', equipment_list['imaging_cameras'][0]['version'])

        self.assertTrue('id' in equipment_list['mounts'][0])
        self.assertEqual('My brand My new mount', equipment_list['mounts'][0]['label'])
        self.assertEqual('NEW', equipment_list['mounts'][0]['version'])

        self.assertTrue('id' in equipment_list['filters'][0])
        self.assertEqual('My brand My new filter', equipment_list['filters'][0]['label'])
        self.assertEqual('NEW', equipment_list['filters'][0]['version'])

        self.assertTrue('id' in equipment_list['accessories'][0])
        self.assertEqual('My brand My new accessory', equipment_list['accessories'][0]['label'])
        self.assertEqual('NEW', equipment_list['accessories'][0]['version'])

        self.assertTrue('id' in equipment_list['software'][0])
        self.assertEqual('My brand My new software', equipment_list['software'][0]['label'])
        self.assertEqual('NEW', equipment_list['software'][0]['version'])

        self.assertTrue('id' in equipment_list['guiding_telescopes'][0])
        self.assertEqual('My brand My new guiding telescope', equipment_list['guiding_telescopes'][0]['label'])
        self.assertEqual('NEW', equipment_list['guiding_telescopes'][0]['version'])

        self.assertTrue('id' in equipment_list['guiding_cameras'][0])
        self.assertEqual('My brand My new guiding camera', equipment_list['guiding_cameras'][0]['label'])
        self.assertEqual('NEW', equipment_list['guiding_cameras'][0]['version'])
        
        self.assertTrue('id' in equipment_list['imaging_telescopes'][1])
        self.assertEqual('My make My imaging telescope', equipment_list['imaging_telescopes'][1]['label'])
        self.assertEqual('LEGACY', equipment_list['imaging_telescopes'][1]['version'])

        self.assertTrue('id' in equipment_list['imaging_cameras'][1])
        self.assertEqual('My make My imaging camera', equipment_list['imaging_cameras'][1]['label'])
        self.assertEqual('LEGACY', equipment_list['imaging_cameras'][1]['version'])

        self.assertTrue('id' in equipment_list['mounts'][1])
        self.assertEqual('My make My mount', equipment_list['mounts'][1]['label'])
        self.assertEqual('LEGACY', equipment_list['mounts'][1]['version'])

        self.assertTrue('id' in equipment_list['filters'][1])
        self.assertEqual('My make My filter', equipment_list['filters'][1]['label'])
        self.assertEqual('LEGACY', equipment_list['filters'][1]['version'])

        self.assertTrue('id' in equipment_list['accessories'][1])
        self.assertEqual('My make My accessory', equipment_list['accessories'][1]['label'])
        self.assertEqual('LEGACY', equipment_list['accessories'][1]['version'])

        self.assertTrue('id' in equipment_list['accessories'][2])
        self.assertEqual('My make My focal reducer', equipment_list['accessories'][2]['label'])
        self.assertEqual('LEGACY', equipment_list['accessories'][2]['version'])

        self.assertTrue('id' in equipment_list['software'][1])
        self.assertEqual('My make My software', equipment_list['software'][1]['label'])
        self.assertEqual('LEGACY', equipment_list['software'][1]['version'])

        self.assertTrue('id' in equipment_list['guiding_telescopes'][1])
        self.assertEqual('My make My guiding telescope', equipment_list['guiding_telescopes'][1]['label'])
        self.assertEqual('LEGACY', equipment_list['guiding_telescopes'][1]['version'])

        self.assertTrue('id' in equipment_list['guiding_cameras'][1])
        self.assertEqual('My make My guiding camera', equipment_list['guiding_cameras'][1]['label'])
        self.assertEqual('LEGACY', equipment_list['guiding_cameras'][1]['version'])

    def test_delete_stories(self):
        image = Generators.image(moderator_decision=ModeratorDecision.APPROVED)

        self.assertEquals(1, Action.objects.action_object(image).count())

        Generators.like(image)

        self.assertEquals(1, Action.objects.action_object(image).count())

        image.delete()

        self.assertEquals(0, Action.objects.action_object(image).count())

    def test_get_collection_tag_value_no_collection(self):
        image = Generators.image()
        self.assertEqual(None, ImageService(image).get_collection_tag_value(None))

    def test_get_collection_tag_value_no_tag(self):
        image = Generators.image()
        collection = Generators.collection()
        self.assertEqual(None, ImageService(image).get_collection_tag_value(collection))

    def test_get_collection_tag_value(self):
        image = Generators.image()
        collection = Generators.collection()
        tag = Generators.key_value_tag(image=image)
        collection.order_by_tag = tag.key
        collection.save()
        self.assertEqual(tag.value, ImageService(image).get_collection_tag_value(collection))

    def test_has_pending_collaborators(self):
        image = Generators.image()
        self.assertFalse(ImageService(image).has_pending_collaborators())

        collaborator = Generators.user()
        image.pending_collaborators.add(collaborator)

        self.assertTrue(ImageService(image).has_pending_collaborators())

        image.collaborators.add(collaborator)

        self.assertFalse(ImageService(image).has_pending_collaborators())
