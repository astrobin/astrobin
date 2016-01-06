# Python
import time

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

# AstroBin
from astrobin.models import (
    Image,
    ImageRevision,
    Telescope,
    Mount,
    Camera,
    FocalReducer,
    Software,
    Filter,
    Accessory,
    DeepSky_Acquisition,
    SolarSystem_Acquisition)


class ImageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'test@test.com', 'password')
        self.user2 = User.objects.create_user(
            'test2', 'test@test.com', 'password')


    def tearDown(self):
        self.user.delete()
        self.user2.delete()


    ###########################################################################
    # HELPERS                                                                 #
    ###########################################################################

    def _do_upload(self, filename, wip = False):
        data = {'image_file': open(filename, 'rb')}
        if wip:
            data['wip'] = True

        return self.client.post(
            reverse('image_upload_process'),
            data,
            follow = True)

    def _do_upload_revision(self, image, filename):
        return self.client.post(
            reverse('image_revision_upload_process'),
            {'image_id': image.id, 'image_file': open(filename, 'rb')},
            follow = True)

    def _get_last_image(self):
        return Image.all_objects.all().order_by('-id')[0]

    def _get_last_image_revision(self):
        return ImageRevision.objects.all().order_by('-id')[0]

    def _assert_message(self, response, tags, content):
        messages = response.context[0]['messages']

        if len(messages) == 0:
            self.assertEqual(False, True)

        for message in messages:
            self.assertEqual(message.tags, tags)
            self.assertTrue(content in message.message)


    ###########################################################################
    # View tests                                                              #
    ###########################################################################

    def test_image_upload_process_view(self):
        self.client.login(username = 'test', password = 'password')

        # Test file with invalid extension
        response = self._do_upload('astrobin/fixtures/invalid_file')
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code = 302,
            target_status_code = 200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test file with invalid content
        response = self._do_upload('astrobin/fixtures/invalid_file.jpg')
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code = 302,
            target_status_code = 200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test failure due to full use of Free membership
        self.user.userprofile.premium_counter = 10
        self.user.userprofile.save()
        response = self._do_upload('astrobin/fixtures/test.jpg')
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code = 302,
            target_status_code = 200)
        self._assert_message(response, "error unread", "Please upgrade")
        self.user.userprofile.premium_counter = 0
        self.user.userprofile.save()

        # Test failure due to read-only mode
        with self.settings(READONLY_MODE = True):
            response = self._do_upload('astrobin/fixtures/test.jpg')
            self.assertRedirects(
                response,
                reverse('image_upload'),
                status_code = 302,
                target_status_code = 200)
            self._assert_message(response, "error unread", "read-only mode")

        # Test missing image file
        response = self.client.post(
            reverse('image_upload_process'),
            follow = True)
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code = 302,
            target_status_code = 200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test indexed PNG
        response = self._do_upload('astrobin/fixtures/test_indexed.png')
        image = self._get_last_image()
        self.assertRedirects(
            response,
            reverse('image_edit_watermark', kwargs = {'id': image.pk}),
            status_code = 302,
            target_status_code = 200)
        self._assert_message(response, "warning unread", "Indexed PNG")
        image.delete()

        # Test WIP
        response = self._do_upload('astrobin/fixtures/test.jpg', wip = True)
        image = self._get_last_image()
        self.assertEqual(image.is_wip, True)
        image.delete()

        # Test successful upload workflow
        response = self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self.assertRedirects(
            response,
            reverse('image_edit_watermark', kwargs = {'id': image.pk}),
            status_code = 302,
            target_status_code = 200)

        self.assertEqual(image.title, u"")

        # Test watermark
        response = self.client.post(
            reverse('image_edit_save_watermark'),
            {
                'image_id': image.pk,
                'watermark': True,
                'watermark_text': "Watermark test",
                'watermark_position': 0,
                'watermark_opacity': 100
            },
            follow = True)
        image = Image.objects.get(pk = image.pk)
        self.assertRedirects(
            response,
            reverse('image_edit_basic', kwargs = {'id': image.pk}),
            status_code = 302,
            target_status_code = 200)
        self.assertEqual(image.watermark, True)
        self.assertEqual(image.watermark_text, "Watermark test")
        self.assertEqual(image.watermark_position, 0)
        self.assertEqual(image.watermark_opacity, 100)

        # Test basic settings
        response = self.client.post(
            reverse('image_edit_save_basic'),
            {
                'image_id': image.pk,
                'submit_gear': True,
                'title': "Test title",
                'link': "http://www.example.com",
                'link_to_fits': "http://www.example.com/fits",
                'subject_type': 600,
                'solar_system_main_subject': 0,
                'locations': [],
                'description': "Image description",
                'allow_comments': True
            },
            follow = True)
        image = Image.objects.get(pk = image.pk)
        self.assertRedirects(
            response,
            reverse('image_edit_gear', kwargs = {'id': image.pk}),
            status_code = 302,
            target_status_code = 200)
        self.assertEqual(image.title, "Test title")
        self.assertEqual(image.link, "http://www.example.com")
        self.assertEqual(image.link_to_fits, "http://www.example.com/fits")
        self.assertEqual(image.subject_type, 600)
        self.assertEqual(image.solar_system_main_subject, 0)
        self.assertEqual(image.locations.count(), 0)
        self.assertEqual(image.description, "Image description")
        self.assertEqual(image.allow_comments, True)

        # Test gear
        imaging_telescopes = [
            Telescope.objects.create(
                make = "Test make", name = "Test imaging telescope")]
        guiding_telescopes = [
            Telescope.objects.create(
                make = "Test make", name = "Test guiding telescope")]
        mounts = [
            Mount.objects.create(
                make = "Test make", name = "Test mount")]
        imaging_cameras = [
            Camera.objects.create(
                make = "Test make", name = "Test imaging camera")]
        guiding_cameras = [
            Camera.objects.create(
                make = "Test make", name = "Test guiding camera")]
        focal_reducers = [
            FocalReducer.objects.create(
                make = "Test make", name = "Test focal reducer")]
        software = [
            Software.objects.create(
                make = "Test make", name = "Test software")]
        filters = [
            Filter.objects.create(
                make = "Test make", name = "Test filter")]
        accessories = [
            Accessory.objects.create(
                make = "Test make", name = "Test accessory")]

        profile = self.user.userprofile
        profile.telescopes = imaging_telescopes + guiding_telescopes
        profile.mounts = mounts
        profile.cameras = imaging_cameras + guiding_cameras
        profile.focal_reducers = focal_reducers
        profile.software = software
        profile.filters = filters
        profile.accessories = accessories

        response = self.client.post(
            reverse('image_edit_save_gear'),
            {
                'image_id': image.pk,
                'submit_acquisition': True,
                'imaging_telescopes': ','.join(["%d" % x.pk for x in imaging_telescopes]),
                'guiding_telescopes': ','.join(["%d" % x.pk for x in guiding_telescopes]),
                'mounts': ','.join(["%d" % x.pk for x in mounts]),
                'imaging_cameras': ','.join(["%d" % x.pk for x in imaging_cameras]),
                'guiding_cameras': ','.join(["%d" % x.pk for x in guiding_cameras]),
                'focal_reducers': ','.join(["%d" % x.pk for x in focal_reducers]),
                'software': ','.join(["%d" % x.pk for x in software]),
                'filters': ','.join(["%d" % x.pk for x in filters]),
                'accessories': ','.join(["%d" % x.pk for x in accessories])
            },
            follow = True)
        image = Image.objects.get(pk = image.pk)
        self.assertRedirects(
            response,
            reverse('image_edit_acquisition', kwargs = {'id': image.pk}),
            status_code = 302,
            target_status_code = 200)

        # Test simple deep sky acquisition
        today = time.strftime('%Y-%m-%d')
        response = self.client.post(
            reverse('image_edit_save_acquisition'),
            {
                'image_id': image.pk,
                'edit_type': 'deep_sky',
                'advanced': 'false',
                'date': today,
                'number': 10,
                'duration': 1200
            },
            follow = True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs = {'id': image.pk}),
            status_code = 302,
            target_status_code = 200)

        image = Image.objects.get(pk = image.pk)
        acquisition = image.acquisition_set.all()[0].deepsky_acquisition
        self.assertEqual(acquisition.date.strftime('%Y-%m-%d'), today)
        self.assertEqual(acquisition.number, 10)
        self.assertEqual(acquisition.duration, 1200)

        for i in imaging_telescopes: i.delete()
        for i in guiding_telescopes: i.delete()
        for i in mounts: i.delete()
        for i in imaging_cameras: i.delete()
        for i in guiding_cameras: i.delete()
        for i in focal_reducers: i.delete()
        for i in software: i.delete()
        for i in filters: i.delete()
        for i in accessories: i.delete()
        image.delete()

    def test_image_detail_view(self):
        self.client.login(username = 'test', password = 'password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        today = time.strftime('%Y-%m-%d')

        # Basic view
        response = self.client.get(reverse('image_detail', kwargs = {'id': image.id}))
        self.assertEqual(response.status_code, 200)

        # Revision redirect
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()
        response = self.client.get(reverse('image_detail', kwargs = {'id': image.id}))
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs = {'id': image.id, 'r': revision.label}),
            status_code = 302,
            target_status_code = 200)
        revision.delete()

        # DSA data
        filter, created = Filter.objects.get_or_create(name = "Test filter")
        dsa, created = DeepSky_Acquisition.objects.get_or_create(
            image = image,
            date = today,
            number = 10,
            duration = 1200,
            filter = filter,
            binning = 1,
            iso = 3200,
            gain = 1,
            sensor_cooling = -20,
            darks = 10,
            flats = 10,
            flat_darks = 10,
            bias = 0,
            bortle = 1,
            mean_sqm = 20.0,
            mean_fwhm = 1,
            temperature = 10)
        response = self.client.get(reverse('image_detail', kwargs = {'id': image.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]['image_type'], 'deep_sky')
        dsa.delete()

        # SSA data
        ssa, created = SolarSystem_Acquisition.objects.get_or_create(
            image = image,
            date = today,
            frames = 1000,
            fps = 60,
            focal_length = 5000,
            cmi = 3,
            cmii = 3,
            cmiii = 3,
            seeing = 1,
            transparency = 1)
        response = self.client.get(reverse('image_detail', kwargs = {'id': image.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]['image_type'], 'solar_system')
        ssa.delete()

        image.delete()

    def test_image_flag_thumbs_view(self):
        self.client.login(username = 'test', password = 'password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        response = self.client.post(
            reverse('image_flag_thumbs', kwargs = {'id': image.id}))
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs = {'id': image.id}),
            status_code = 302,
            target_status_code = 302) # target 302 due to revision redirect

        revision.delete()
        image.delete()

    def test_image_thumb_view(self):
        self.client.login(username = 'test', password = 'password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        response = self.client.get(
            reverse('image_thumb', kwargs = {
                'id': image.id,
                'alias': 'regular'
            }))
        self.assertEqual(response.status_code, 200)
        image.delete()

    def test_image_rawthumb_view(self):
        self.client.login(username = 'test', password = 'password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        response = self.client.get(
            reverse('image_rawthumb', kwargs = {
                'id': image.id,
                'alias': 'regular'
            }),
            follow = True)
        self.assertRedirects(
            response,
            image.thumbnail('regular'),
            status_code = 302,
            target_status_code = 200)
        image.delete()

    def test_image_full_view(self):
        self.client.login(username = 'test', password = 'password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        response = self.client.get(reverse('image_full', kwargs = {'id': image.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]['alias'], 'hd')

        # Revision redirect
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()
        response = self.client.get(reverse('image_full', kwargs = {'id': image.id}))
        self.assertRedirects(
            response,
            reverse('image_full', kwargs = {'id': image.id, 'r': revision.label}),
            status_code = 302,
            target_status_code = 200)
        revision.delete()

        # Mods
        response = self.client.get(
            reverse('image_full', kwargs = {'id': image.id}) + "?mod=inverted")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]['mod'], 'inverted')
        self.assertEqual(response.context[0]['alias'], 'hd_inverted')

        # Real
        response = self.client.get(
            reverse('image_full', kwargs = {'id': image.id}) + "?real")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]['alias'], 'real')


        image.delete()

    def test_image_upload_revision_process_view(self):
        self.client.login(username = 'test', password = 'password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        # Test file with invalid extension
        response = self._do_upload_revision(image, 'astrobin/fixtures/invalid_file')
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs = {'id': image.id}),
            status_code = 302,
            target_status_code = 200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test file with invalid content
        response = self._do_upload_revision(image, 'astrobin/fixtures/invalid_file.jpg')
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs = {'id': image.id}),
            status_code = 302,
            target_status_code = 200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test successful upload
        response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs = {'id': image.id, 'r': 'B'}),
            status_code = 302,
            target_status_code = 200)
        self._assert_message(response, "success unread", "Image uploaded")
        image = self._get_last_image()
        revision = self._get_last_image_revision()
        self.assertEqual(image.revisions.count(), 1)

        revision.delete()
        image.delete()

    def test_image_edit_make_final_view(self):
        self.client.login(username = 'test', password = 'password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        response = self.client.get(
            reverse('image_edit_make_final', kwargs = {'id': image.id}),
            follow = True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs = {'id': 1}),
            status_code = 302,
            target_status_code = 200)
        image = self._get_last_image()
        revision = self._get_last_image_revision()
        self.assertEqual(image.is_final, True)
        self.assertEqual(image.revisions.all()[0].is_final, False)

        revision.delete()
        image.delete()

    def test_image_edit_revision_make_final_view(self):
        self.client.login(username = 'test', password = 'password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        # Upload revision B
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')

        # Upload revision C
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')

        # Check that C is final
        image = self._get_last_image()
        c = image.revisions.order_by('-label')[0]
        b = image.revisions.order_by('-label')[1]
        self.assertEqual(image.is_final, False)
        self.assertEqual(c.is_final, True)
        self.assertEqual(b.is_final, False)

        # Make B final
        response = self.client.get(
            reverse('image_edit_revision_make_final', kwargs = {'id': b.id}),
            follow = True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs = {'id': 1, 'r': b.label}),
            status_code = 302,
            target_status_code = 200)

        # Check that B is now final
        image = self._get_last_image()
        c = image.revisions.order_by('-label')[0]
        b = image.revisions.order_by('-label')[1]
        self.assertEqual(image.is_final, False)
        self.assertEqual(c.is_final, False)
        self.assertEqual(b.is_final, True)

        b.delete()
        c.delete()
        image.delete()

    def test_image_edit_basic_view(self):
        self.client.login(username = 'test', password = 'password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self.client.logout()

        # GET
        self.client.login(username = 'test2', password = 'password')
        response = self.client.get(
            reverse('image_edit_basic', args = (image.pk,)))
        self.assertEqual(response.status_code, 403)

        # POST
        response = self.client.post(
            reverse('image_edit_save_basic'),
            {
                'image_id': image.pk,
                'title': "Test title",
                'link': "http://www.example.com",
                'link_to_fits': "http://www.example.com/fits",
                'subject_type': 600,
                'solar_system_main_subject': 0,
                'locations': [],
                'description': "Image description",
                'allow_comments': True
            },
            follow = True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # GET
        self.client.login(username = 'test', password = 'password')
        response = self.client.get(
            reverse('image_edit_basic', args = (image.pk,)))
        self.assertEqual(response.status_code, 200)

        # POST
        response = self.client.post(
            reverse('image_edit_save_basic'),
            {
                'image_id': image.pk,
                'title': "Test title",
                'link': "http://www.example.com",
                'link_to_fits': "http://www.example.com/fits",
                'subject_type': 600,
                'solar_system_main_subject': 0,
                'locations': [],
                'description': "Image description",
                'allow_comments': True
            },
            follow = True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs = {'id': image.pk}),
            status_code = 302,
            target_status_code = 200)

        # Missing image_id in post
        response = self.client.post(reverse('image_edit_save_basic'), {})
        self.assertEqual(response.status_code, 404)

        # Invalid form
        response = self.client.post(
            reverse('image_edit_save_basic'), {'image_id': image.pk})
        self.assertEqual(response.status_code, 200)
        self._assert_message(response, "error unread", "errors processing the form")
        self.client.logout()

        # Anonymous GET
        response = self.client.get(
            reverse('image_edit_basic', args = (image.pk,)))
        self.assertRedirects(
            response,
            '/accounts/login/?next=' +
            reverse('image_edit_basic', args = (image.pk,)),
            status_code = 302,
            target_status_code = 200)

        # Anonymous POST
        response = self.client.post(
            reverse('image_edit_save_basic'),
            {
                'image_id': image.pk,
                'title': "Test title",
                'link': "http://www.example.com",
                'link_to_fits': "http://www.example.com/fits",
                'subject_type': 600,
                'solar_system_main_subject': 0,
                'locations': [],
                'description': "Image description",
                'allow_comments': True
            },
            follow = True)
        self.assertRedirects(
            response,
            '/accounts/login/?next=' + reverse('image_edit_save_basic'),
            status_code = 302,
            target_status_code = 200)

        image.delete()
