# Python
import time

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

# AstroBin
from astrobin.models import (
    Image,
    Telescope,
    Mount,
    Camera,
    FocalReducer,
    Software,
    Filter,
    Accessory,
    DeepSky_Acquisition)


class ImageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'test@test.com', 'password')

    def tearDown(self):
        self.user.delete()

    def _do_upload(self, filename):
        return self.client.post(
            reverse('image_upload_process'),
            {'image_file': open(filename, 'rb')},
            follow = True)

    def _assert_message(self, response, tags, content):
        storage = response.context[0]['messages']
        for message in storage:
            self.assertEqual(message.tags, tags)
            self.assertTrue(content in message.message)

    def test_upload(self):
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

        # Test successful upload
        response = self._do_upload('astrobin/fixtures/test.jpg')
        self.assertRedirects(
            response,
            reverse('image_edit_watermark', kwargs = {'id': 1}),
            status_code = 302,
            target_status_code = 200)

        image = Image.objects.get(pk = 1)
        self.assertEqual(image.title, u"")

        # Test watermark
        response = self.client.post(
            reverse('image_edit_save_watermark'),
            {
                'image_id': 1,
                'watermark': True,
                'watermark_text': "Watermark test",
                'watermark_position': 0,
                'watermark_opacity': 100
            },
            follow = True)
        image = Image.objects.get(pk = 1)
        self.assertRedirects(
            response,
            reverse('image_edit_basic', kwargs = {'id': 1}),
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
                'image_id': 1,
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
        image = Image.objects.get(pk = 1)
        self.assertRedirects(
            response,
            reverse('image_edit_gear', kwargs = {'id': 1}),
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
                'image_id': 1,
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
        image = Image.objects.get(pk = 1)
        self.assertRedirects(
            response,
            reverse('image_edit_acquisition', kwargs = {'id': 1}),
            status_code = 302,
            target_status_code = 200)

        # Test simple deep sky acquisition
        today = time.strftime('%Y-%m-%d')
        response = self.client.post(
            reverse('image_edit_save_acquisition'),
            {
                'image_id': 1,
                'edit_type': 'deep_sky',
                'advanced': 'false',
                'date': today,
                'number': 10,
                'duration': 1200
            },
            follow = True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs = {'id': 1}),
            status_code = 302,
            target_status_code = 200)

        image = Image.objects.get(pk = 1)
        acquisition = image.acquisition_set.all()[0].deepsky_acquisition
        self.assertEqual(acquisition.date.strftime('%Y-%m-%d'), today)
        self.assertEqual(acquisition.number, 10)
        self.assertEqual(acquisition.duration, 1200)

        image.delete()

    def test_detail(self):
        self.client.login(username = 'test', password = 'password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = Image.objects.all().order_by('-id')[0]
        response = self.client.get(reverse('image_detail', kwargs = {'id': image.id}))
        self.assertEqual(response.status_code, 200)
