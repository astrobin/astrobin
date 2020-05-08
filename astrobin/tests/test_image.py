# -*- coding: UTF-8

import re
import sys
import time
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from mock import patch
from subscription.models import Subscription, UserSubscription

from astrobin.enums import SubjectType
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
    SolarSystem_Acquisition,
    Location)
from astrobin.tests.generators import Generators
from astrobin_apps_groups.models import Group as AstroBinGroup
from astrobin_apps_notifications.utils import get_unseen_notifications
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.solver import Solver
from nested_comments.models import NestedComment
from toggleproperties.models import ToggleProperty


class ImageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'test@test.com', 'password')
        self.user2 = User.objects.create_user(
            'test2', 'test@test.com', 'password')

        # Test gear
        self.imaging_telescopes = [
            Telescope.objects.create(
                make="Test make", name="Test imaging telescope")]
        self.guiding_telescopes = [
            Telescope.objects.create(
                make="Test make", name="Test guiding telescope")]
        self.mounts = [
            Mount.objects.create(
                make="Test make", name="Test mount")]
        self.imaging_cameras = [
            Camera.objects.create(
                make="Test make", name="Test imaging camera")]
        self.guiding_cameras = [
            Camera.objects.create(
                make="Test make", name="Test guiding camera")]
        self.focal_reducers = [
            FocalReducer.objects.create(
                make="Test make", name="Test focal reducer")]
        self.software = [
            Software.objects.create(
                make="Test make", name="Test software")]
        self.filters = [
            Filter.objects.create(
                make="Test make", name="Test filter")]
        self.accessories = [
            Accessory.objects.create(
                make="Test make", name="Test accessory")]

        profile = self.user.userprofile
        profile.telescopes = self.imaging_telescopes + self.guiding_telescopes
        profile.mounts = self.mounts
        profile.cameras = self.imaging_cameras + self.guiding_cameras
        profile.focal_reducers = self.focal_reducers
        profile.software = self.software
        profile.filters = self.filters
        profile.accessories = self.accessories

    def tearDown(self):
        for i in self.imaging_telescopes: i.delete()
        for i in self.guiding_telescopes: i.delete()
        for i in self.mounts: i.delete()
        for i in self.imaging_cameras: i.delete()
        for i in self.guiding_cameras: i.delete()
        for i in self.focal_reducers: i.delete()
        for i in self.software: i.delete()
        for i in self.filters: i.delete()
        for i in self.accessories: i.delete()

        self.user.delete()
        self.user2.delete()

    ###########################################################################
    # HELPERS                                                                 #
    ###########################################################################

    def _do_upload(self, filename, wip=False):
        # type: (basestring, bool, bool) -> None

        data = {'image_file': open(filename, 'rb')}

        if wip:
            data['wip'] = True

        return self.client.post(
            reverse('image_upload_process'),
            data,
            follow=True)

    def _do_upload_revision(self, image, filename, description=None, skip_notifications=False, mark_as_final=True):
        data = {
            'image_id': image.get_id(),
            'image_file': open(filename, 'rb'),
            'description': description,
        }

        if skip_notifications:
            data['skip_notifications'] = True

        if mark_as_final:
            data['mark_as_final'] = u'on'

        return self.client.post(
            reverse('image_revision_upload_process'),
            data,
            follow=True)

    def _get_last_image(self):
        return Image.objects_including_wip.all().order_by('-id')[0]

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

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_process_view(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')

        # Test file with invalid extension
        response = self._do_upload('astrobin/fixtures/invalid_file')
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test file with invalid content
        response = self._do_upload('astrobin/fixtures/invalid_file.jpg')
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test failure due to full use of Free membership
        self.user.userprofile.premium_counter = settings.PREMIUM_MAX_IMAGES_FREE
        self.user.userprofile.save(keep_deleted=True)
        response = self._do_upload('astrobin/fixtures/test.jpg')
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "error unread", "Please upgrade")
        self.user.userprofile.premium_counter = 0
        self.user.userprofile.save(keep_deleted=True)

        # Test failure due to read-only mode
        with self.settings(READONLY_MODE=True):
            response = self._do_upload('astrobin/fixtures/test.jpg')
            self.assertRedirects(
                response,
                reverse('image_upload'),
                status_code=302,
                target_status_code=200)
            self._assert_message(response, "error unread", "read-only mode")

        # Test missing image file
        response = self.client.post(
            reverse('image_upload_process'),
            follow=True)
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test indexed PNG
        response = self._do_upload('astrobin/fixtures/test_indexed.png')
        image = self._get_last_image()
        self.assertRedirects(
            response,
            reverse('image_edit_thumbnails', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "warning unread", "Indexed PNG")
        image.delete()

        # Test WIP
        response = self._do_upload('astrobin/fixtures/test.jpg', wip=True)
        image = self._get_last_image()
        self.assertEqual(image.is_wip, True)
        self.assertIsNone(image.published)
        image.delete()

        # Test successful upload workflow
        response = self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self.assertRedirects(
            response,
            reverse('image_edit_thumbnails', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)

        self.assertEqual(image.title, u"")
        self.assertTrue((image.published - image.uploaded).total_seconds() < 1)

        # Test thumbnails
        response = self.client.post(
            reverse('image_edit_thumbnails', kwargs={'id': image.get_id()}),
            {
                'image_id': image.get_id(),
                'square_cropping': '100, 0, 100, 0',
                'submit_watermark': True,
            },
            follow=True)
        image = Image.objects.get(pk=image.pk)
        self.assertRedirects(
            response,
            reverse('image_edit_watermark', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)

        # Test watermark
        response = self.client.post(
            reverse('image_edit_save_watermark'),
            {
                'image_id': image.get_id(),
                'watermark': True,
                'watermark_text': "Watermark test",
                'watermark_position': 0,
                'watermark_size': 'S',
                'watermark_opacity': 100
            },
            follow=True)
        self.assertRedirects(
            response,
            reverse('image_edit_basic', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        image = Image.objects.get(pk=image.pk)
        self.assertEqual(image.watermark, True)
        self.assertEqual(image.watermark_text, "Watermark test")
        self.assertEqual(image.watermark_position, 0)
        self.assertEqual(image.watermark_size, 'S')
        self.assertEqual(image.watermark_opacity, 100)

        # Test basic settings

        location, created = Location.objects.get_or_create(
            name="Test location")
        self.user.userprofile.location_set.add(location)

        # Test missing data_source
        response = self.client.post(
            reverse('image_edit_basic', args=(image.get_id(),)),
            {
                'submit_gear': True,
                'title': "Test title",
                'link': "http://www.example.com",
                'link_to_fits': "http://www.example.com/fits",
                'acquisition_type': 'TRADITIONAL',
                'subject_type': SubjectType.OTHER,
                'locations': [location.pk],
                'description': "Image description",
                'allow_comments': True
            },
            follow=True)
        self._assert_message(response, "error unread", "There was one or more errors processing the form")

        # Test missing remote_source
        response = self.client.post(
            reverse('image_edit_basic', args=(image.get_id(),)),
            {
                'submit_gear': True,
                'title': "Test title",
                'link': "http://www.example.com",
                'link_to_fits': "http://www.example.com/fits",
                'acquisition_type': 'TRADITIONAL',
                'data_source': 'AMATEUR_HOSTING',
                'subject_type': SubjectType.OTHER,
                'locations': [location.pk],
                'description': "Image description",
                'allow_comments': True
            },
            follow=True)
        self._assert_message(response, "error unread", "There was one or more errors processing the form")

        response = self.client.post(
            reverse('image_edit_basic', args=(image.get_id(),)),
            {
                'submit_gear': True,
                'title': "Test title",
                'link': "http://www.example.com",
                'link_to_fits': "http://www.example.com/fits",
                'acquisition_type': 'TRADITIONAL',
                'data_source': 'OTHER',
                'subject_type': SubjectType.OTHER,
                'locations': [location.pk],
                'description': "Image description",
                'allow_comments': True
            },
            follow=True)
        image = Image.objects.get(pk=image.pk)
        self.assertRedirects(
            response,
            reverse('image_edit_gear', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self.assertEqual(image.title, "Test title")
        self.assertEqual(image.link, "http://www.example.com")
        self.assertEqual(image.link_to_fits, "http://www.example.com/fits")
        self.assertEqual(image.subject_type, SubjectType.OTHER)
        self.assertEqual(image.solar_system_main_subject, None)
        self.assertEqual(image.locations.count(), 1)
        self.assertEqual(image.locations.all().first().pk, location.pk)
        self.assertEqual(image.description, "Image description")
        self.assertEqual(image.allow_comments, True)
        self.user.userprofile.location_set.clear()

        response = self.client.post(
            reverse('image_edit_gear', args=(image.get_id(),)),
            {
                'image_id': image.pk,
                'submit_acquisition': True,
                'imaging_telescopes': ','.join(["%d" % x.pk for x in self.imaging_telescopes]),
                'guiding_telescopes': ','.join(["%d" % x.pk for x in self.guiding_telescopes]),
                'mounts': ','.join(["%d" % x.pk for x in self.mounts]),
                'imaging_cameras': ','.join(["%d" % x.pk for x in self.imaging_cameras]),
                'guiding_cameras': ','.join(["%d" % x.pk for x in self.guiding_cameras]),
                'focal_reducers': ','.join(["%d" % x.pk for x in self.focal_reducers]),
                'software': ','.join(["%d" % x.pk for x in self.software]),
                'filters': ','.join(["%d" % x.pk for x in self.filters]),
                'accessories': ','.join(["%d" % x.pk for x in self.accessories])
            },
            follow=True)
        image = Image.objects.get(pk=image.pk)
        self.assertRedirects(
            response,
            reverse('image_edit_acquisition', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)

        # Test simple deep sky acquisition
        today = time.strftime('%Y-%m-%d')
        response = self.client.post(
            reverse('image_edit_save_acquisition'),
            {
                'image_id': image.get_id(),
                'edit_type': 'deep_sky',
                'advanced': 'false',
                'date': today,
                'number': 10,
                'duration': 1200
            },
            follow=True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)

        image = Image.objects.get(pk=image.pk)
        acquisition = image.acquisition_set.all()[0].deepsky_acquisition
        self.assertEqual(acquisition.date.strftime('%Y-%m-%d'), today)
        self.assertEqual(acquisition.number, 10)
        self.assertEqual(acquisition.duration, 1200)

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @patch("astrobin.signals.push_notification")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_upload_process_view_skip_notifications(self, push_notification, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')

        ToggleProperty.objects.create(
            property_type='follow',
            user=self.user2,
            content_object=self.user
        )

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self.assertTrue(push_notification.called)
        push_notification.reset_mock()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg', skip_notifications=True)
        self.assertFalse(push_notification.called)

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_upload_process_view_dont_mark_as_final(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg', mark_as_final=False)
        revision = self._get_last_image_revision()

        self.assertTrue(image.is_final)
        self.assertFalse(revision.is_final)

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_process_view_image_too_large_free(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_FREE_2020=10 * 1024):
            response = self._do_upload('astrobin/fixtures/test.jpg')
            self.assertContains(response, "this image is too large")
            self.assertContains(response, "maximum allowed image size is 10.0")

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_process_view_image_too_large_lite(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        us = Generators.premium_subscription(self.user, "AstroBin Lite")

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_LITE_2020=1):
            response = self._do_upload('astrobin/fixtures/test.jpg')
            self.assertNotContains(response, "this image is too large")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_process_view_image_too_large_lite_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        us = Generators.premium_subscription(self.user, "AstroBin Lite 2020+")

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_LITE_2020=10 * 1024):
            response = self._do_upload('astrobin/fixtures/test.jpg')
            self.assertContains(response, "this image is too large")
            self.assertContains(response, "maximum allowed image size is 10.0")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_process_view_image_too_large_premium(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        us = Generators.premium_subscription(self.user, "AstroBin Premium")

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020=1):
            response = self._do_upload('astrobin/fixtures/test.jpg')
            self.assertNotContains(response, "this image is too large")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_process_view_image_too_large_premium_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        us = Generators.premium_subscription(self.user, "AstroBin Premium 2020+")

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020=10 * 1024):
            response = self._do_upload('astrobin/fixtures/test.jpg')
            self.assertContains(response, "this image is too large")
            self.assertContains(response, "maximum allowed image size is 10.0")

        us.delete()

    def test_image_upload_process_view_inactive_subscription(self):
        self.client.login(username='test', password='password')
        premium = Generators.premium_subscription(self.user, "AstroBin Premium 2020+")

        response = self.client.get(reverse('image_upload'))
        self.assertNotContains(response, "Your Lite or Premium subscription is not active")

        premium.expires = date.today() - timedelta(1)
        premium.save()

        response = self.client.get(reverse('image_upload'))
        self.assertContains(response, "Your Lite or Premium subscription is not active")

        premium.expires = date.today() + timedelta(1)
        premium.save()

        ultimate = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        ultimate.expires = date.today() - timedelta(1)
        ultimate.save()

        response = self.client.get(reverse('image_upload'))
        self.assertNotContains(response, "Your Lite or Premium subscription is not active")

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_process_view_image_too_large_ultimate_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        us = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020=1):
            response = self._do_upload('astrobin/fixtures/test.jpg')
            self.assertNotContains(response, "this image is too large")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    @override_settings(PREMIUM_MAX_IMAGE_SIZE_FREE_2020=sys.maxsize)
    def test_image_upload_revision_process_view_image_too_large_free(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_FREE_2020=10 * 1024):
            response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
            self.assertContains(response, "this image is too large")
            self.assertContains(response, "maximum allowed image size is 10.0")

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    @override_settings(PREMIUM_MAX_IMAGE_SIZE_FREE_2020=sys.maxsize)
    def test_image_upload_revision_process_view_image_too_large_lite(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Lite")

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_LITE_2020=10 * 1024):
            response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
            self.assertNotContains(response, "this image is too large")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    @override_settings(PREMIUM_MAX_IMAGE_SIZE_FREE_2020=sys.maxsize)
    def test_image_upload_revision_process_view_image_too_large_lite_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Lite 2020+")

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_LITE_2020=10 * 1024):
            response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
            self.assertContains(response, "this image is too large")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    @override_settings(PREMIUM_MAX_IMAGE_SIZE_FREE_2020=sys.maxsize)
    def test_image_upload_revision_process_view_image_too_large_premium(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Premium")

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020=10 * 1024):
            response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
            self.assertNotContains(response, "this image is too large")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    @override_settings(PREMIUM_MAX_IMAGE_SIZE_FREE_2020=sys.maxsize)
    def test_image_upload_revision_process_view_image_too_large_premium_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Premium 2020+")

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020=10 * 1024):
            response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
            self.assertContains(response, "this image is too large")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    @override_settings(PREMIUM_MAX_IMAGE_SIZE_FREE_2020=sys.maxsize)
    def test_image_upload_revision_process_view_image_too_large_ultimate_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")

        with self.settings(PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020=10 * 1024):
            response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
            self.assertNotContains(response, "this image is too large")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_revision_process_view_too_many_revisions_free(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        self.assertContains(response, "you have reached the maximum amount of allowed image revisions")
        self.assertContains(response, "Under your current subscription, the limit is 0 revisions per image")

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_revision_process_view_too_many_revisions_premium(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Premium")

        response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        self.assertContains(response, "Image uploaded. Thank you!")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_revision_process_view_too_many_revisions_lite_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Lite 2020+")

        response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        self.assertContains(response, "Image uploaded. Thank you!")

        response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        self.assertContains(response, "you have reached the maximum amount of allowed image revisions")
        self.assertContains(response, "Under your current subscription, the limit is 1 revision per image")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_upload_revision_process_view_too_many_revisions_premium_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Premium 2020+")

        response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        self.assertContains(response, "Image uploaded. Thank you!")

        with self.settings(PREMIUM_MAX_REVISIONS_PREMIUM_2020=1):
            response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
            self.assertContains(response, "you have reached the maximum amount of allowed image revisions")
            self.assertContains(response, "Under your current subscription, the limit is 1 revision per image")

        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_detail_view_original_revision_overlay(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        Solution.objects.create(
            status=Solver.SUCCESS,
            content_object=image
        )

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg', "Test revision description")
        revision = self._get_last_image_revision()

        image.mouse_hover_image = "REVISION__%s" % revision.label
        image.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "hover-overlay-original-revision")
        self.assertNotContains(response, "hover-overlay-solution")

        image.delete()
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_detail_view_original_solution_overlay(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        Solution.objects.create(
            status=Solver.SUCCESS,
            content_object=image
        )

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "hover-overlay-solution")

        image.delete()
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_detail_view_original_inverted_overlay(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        Solution.objects.create(
            status=Solver.SUCCESS,
            content_object=image
        )

        image.mouse_hover_image = "INVERTED"
        image.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "hover-overlay-original-inverted")
        self.assertNotContains(response, "hover-overlay-solution")

        image.delete()
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_detail_view_revision_original_overlay(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg', "Test revision description")
        revision = self._get_last_image_revision()

        Solution.objects.create(
            status=Solver.SUCCESS,
            content_object=revision
        )

        revision.mouse_hover_image = "ORIGINAL"
        revision.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), "r": revision.label}))
        self.assertContains(response, "hover-overlay-revision-original")
        self.assertNotContains(response, "hover-overlay-solution")

        image.delete()
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_detail_view_revision_solution_overlay(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg', "Test revision description")
        revision = self._get_last_image_revision()

        Solution.objects.create(
            status=Solver.SUCCESS,
            content_object=revision
        )

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), "r": revision.label}))
        self.assertContains(response, "hover-overlay-solution")

        image.delete()
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_detail_view_revision_revision_overlay(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg', "Test revision description")
        revision = self._get_last_image_revision()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg', "Test revision description")
        revision2 = self._get_last_image_revision()

        Solution.objects.create(
            status=Solver.SUCCESS,
            content_object=revision
        )

        revision.mouse_hover_image = "REVISION__%s" % revision2.label
        revision.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), "r": revision.label}))
        self.assertContains(response, "hover-overlay-revision-revision")
        self.assertNotContains(response, "hover-overlay-solution")

        image.delete()
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_detail_view_revision_inverted_overlay(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg', "Test revision description")
        revision = self._get_last_image_revision()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg', "Test revision description")
        revision2 = self._get_last_image_revision()

        Solution.objects.create(
            status=Solver.SUCCESS,
            content_object=revision
        )

        revision.mouse_hover_image = "INVERTED"
        revision.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), "r": revision.label}))
        self.assertContains(response, "hover-overlay-revision-inverted")
        self.assertNotContains(response, "hover-overlay-solution")

        image.delete()
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_detail_view(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.subject_type = SubjectType.DEEP_SKY
        image.save(keep_deleted=True)
        today = time.strftime('%Y-%m-%d')

        # Basic view
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(re.search(r'data-id="%s"\s+data-alias="%s"' % (image.pk, "regular"), response.content))

        # Image resolution
        self.assertContains(response, "<strong class=\"card-label\">Resolution:</strong> 340x280")

        # Revision redirect
        self._do_upload_revision(image, 'astrobin/fixtures/test_smaller.jpg')
        revision = self._get_last_image_revision()
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id(), 'r': revision.label}),
            status_code=302,
            target_status_code=200)

        # Correct revision displayed
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': 'B'}))
        self.assertIsNotNone(re.search(
            r'data-id="%d"\s+data-alias="%s"\s+data-revision="%s"' % (image.pk, "regular", "B"),
            response.content))
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "thumb"), response.content))

        # Revision resolution differs from original
        self.assertContains(response, "<strong class=\"card-label\">Resolution:</strong> 200x165")

        # Revision description displayed
        desc = "Test revision description"
        revision.description = desc
        revision.save(keep_deleted=True)
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': 'B'}))
        self.assertContains(response, desc)

        # If description is set to empty text, then it's gone
        revision.description = ''
        revision.save(keep_deleted=True)
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': 'B'}))
        self.assertNotContains(response, desc)
        self.assertNotContains(response, '<h3>%s</h3>' % revision.label, html=True)

        # Correct revision displayed in gallery
        response = self.client.get(reverse('user_page', kwargs={'username': 'test'}))
        self.assertIsNotNone(re.search(
            r'data-id="%d"\s+data-alias="%s"\s+data-revision="%s"' % (image.pk, "gallery", "final"),
            response.content))

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': '0'}))
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "regular"), response.content))
        self.assertIsNotNone(re.search(
            r'data-id="%d"\s+data-alias="%s"\s+data-revision="%s"' % (image.pk, "thumb", "B"),
            response.content))

        # Inverted displayed
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': '0'}) + "?mod=inverted")
        self.assertIsNotNone(
            re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "regular_inverted"), response.content))

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': 'B'}) + "?mod=inverted")
        self.assertIsNotNone(re.search(
            r'data-id="%d"\s+data-alias="%s"\s+data-revision="%s"' % (image.pk, "regular_inverted", "B"),
            response.content))

        revision.delete()

        # DSA data
        filter, created = Filter.objects.get_or_create(name="Test filter")
        dsa, created = DeepSky_Acquisition.objects.get_or_create(
            image=image,
            date=today,
            number=10,
            duration=1200,
            filter=filter,
            binning=1,
            iso=3200,
            gain=1.00,
            sensor_cooling=-20,
            darks=10,
            flats=10,
            flat_darks=10,
            bias=0,
            bortle=1,
            mean_sqm=20.0,
            mean_fwhm=1,
            temperature=10)
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]['image_type'], 'deep_sky')

        dsa.delete()

        # SSA data
        ssa, created = SolarSystem_Acquisition.objects.get_or_create(
            image=image,
            date=today,
            frames=1000,
            fps=60,
            focal_length=5000,
            cmi=3,
            cmii=3,
            cmiii=3,
            seeing=1,
            transparency=1)
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]['image_type'], 'solar_system')
        ssa.delete()

        # Test whether the Like button is active: image owner can't like
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.context[0]['user_can_like'], False)

        # Test whether the Like button is active: index 0 can't like
        self.client.logout()
        self.client.login(username='test2', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.context[0]['user_can_like'], False)

        # Test whether the Like button is active: index 0 but Premium can like
        g, created = Group.objects.get_or_create(name="astrobin_premium")
        s, created = Subscription.objects.get_or_create(
            name="AstroBin Premium",
            price=1,
            group=g,
            category="premium")
        us, created = UserSubscription.objects.get_or_create(
            user=self.user2,
            subscription=s)
        us.subscribe()
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.context[0]['user_can_like'], True)

        # Spam images should be 404
        image.moderator_decision = 2
        image.save(keep_deleted=True)
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.status_code, 404)

        # Except for moderators, they can see them
        moderators, created = Group.objects.get_or_create(name='image_moderators')
        self.user2.groups.add(moderators)
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.status_code, 200)
        self.user2.groups.remove(moderators)

        # And except for superusers
        self.user2.is_superuser = True
        self.user2.save()
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.status_code, 200)
        self.user2.is_superuser = False
        self.user2.save()

        # Anon users get 404 of course
        self.client.logout()
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.status_code, 404)

        us.unsubscribe()
        us.delete()
        s.delete()
        g.delete()

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_7_digit_gain(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.subject_type = SubjectType.DEEP_SKY
        image.save(keep_deleted=True)
        today = time.strftime('%Y-%m-%d')

        us = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")

        # DSA data
        dsa, created = DeepSky_Acquisition.objects.get_or_create(
            image=image,
            date=today,
            number=10,
            duration=1200,
            gain=12345.67,
        )
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "(gain: 12345.67)")

        dsa.delete()
        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_flag_thumbs_view(self, retrieve_primary_thumbnails):
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        response = self.client.post(
            reverse('image_flag_thumbs', kwargs={'id': image.get_id()}))
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={
                'id': image.get_id(),
                'r': 'B',
            }),
            status_code=302,
            target_status_code=200)

        revision.delete()
        image.delete()
        self.client.logout()
        self.user.is_superuser = False
        self.user.save()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @patch("astrobin.tasks.retrieve_thumbnail")
    def test_image_thumb_view(self, retrieve_primary_thumbnails, retrieve_thumbnail):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        response = self.client.get(
            reverse('image_thumb', kwargs={
                'id': image.get_id(),
                'alias': 'regular'
            }))
        self.assertEqual(response.status_code, 200)
        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @patch("astrobin.tasks.retrieve_thumbnail")
    def test_image_rawthumb_view(self, retrieve_primary_thumbnails, retrieve_thumbnail):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        opts = {
            'id': image.get_id(),
            'alias': 'regular'
        }

        def get_expected_url(image):
            thumb = image.thumbnail_raw(opts['alias'], {
                'revision_label': 0,
                'animated': False,
                'insecure': False
            })
            return thumb.url

        response = self.client.get(reverse('image_rawthumb', kwargs=opts), follow=True)
        # 404 because we don't serve that /media/static file, that's fine.
        self.assertRedirects(response, get_expected_url(image))

        # Set the watermark to some non ASCII symbol
        image.watermark_text = "©"
        image.watermark = True
        image.save(keep_deleted=True)

        image = Image.objects.get(pk=image.pk)
        response = self.client.get(reverse('image_rawthumb', kwargs=opts), follow=True)
        self.assertRedirects(response, get_expected_url(image))

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_full_view(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id()}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]['alias'], 'hd')
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "hd"), response.content))

        # Revision redirect
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()
        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id()}))
        self.assertRedirects(
            response,
            reverse('image_full', kwargs={'id': image.get_id(), 'r': revision.label}),
            status_code=302,
            target_status_code=200)

        # Correct revision displayed
        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id(), 'r': 'B'}))
        self.assertIsNotNone(re.search(
            r'data-id="%d"\s+data-alias="%s"\s+data-revision="%s"' % (image.pk, "hd", "B"),
            response.content))
        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id(), 'r': '0'}))
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "hd"), response.content))

        revision.delete()

        # Mods
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?mod=inverted")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]['mod'], 'inverted')
        self.assertEqual(response.context[0]['alias'], 'hd_inverted')
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "hd_inverted"), response.content))

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_owner(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_visitor(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()
        image = self._get_last_image()

        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('hd', response.context[0]['alias'])
        self.assertIsNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_free(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('hd', response.context[0]['alias'])
        self.assertIsNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_lite(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user2, "AstroBin Lite")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_lite_autorenew(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user2, "AstroBin Lite (autorenew)")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_lite_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self.client.logout()

        us = Generators.premium_subscription(self.user2, "AstroBin Lite 2020+")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_premium(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user2, "AstroBin Premium")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_premium_autorenew(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user2, "AstroBin Premium (autorenew)")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_premium_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user2, "AstroBin Premium 2020+")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_ultimate_2020(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user2, "AstroBin Ultimate 2020+")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_ultimate_2020_owner(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_premium_owner(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Premium")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_premium_autorenew_owner(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Premium (autorenew)")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_ilte_owner(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Lite")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_real_view_lite_autorenew_owner(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()

        us = Generators.premium_subscription(self.user, "AstroBin Lite (autorenew)")

        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id()}) + "?real")
        self.assertEqual(200, response.status_code)
        self.assertEqual('real', response.context[0]['alias'])
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image.pk, "real"), response.content))

        image.delete()
        us.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_upload_revision_process_view(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        # Test file with invalid extension
        response = self._do_upload_revision(image, 'astrobin/fixtures/invalid_file')
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test file with invalid content
        response = self._do_upload_revision(image, 'astrobin/fixtures/invalid_file.jpg')
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test successful upload
        response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id(), 'r': 'B'}),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "success unread", "Image uploaded")
        image = self._get_last_image()
        revision = self._get_last_image_revision()
        self.assertEqual(1, image.revisions.count())
        self.assertEqual('B', revision.label)

        # Now delete B and see that the new one gets C because B is soft-deleted
        revision.delete()
        with self.assertRaises(ImageRevision.DoesNotExist):
            revision = ImageRevision.objects.get(pk=revision.pk)
        revision = ImageRevision.all_objects.get(pk=revision.pk)
        self.assertNotEqual(None, revision.deleted)
        self.assertEqual(0, ImageRevision.objects.filter(image=image).count())
        image = Image.objects.get(pk=image.pk)
        self.assertEqual(0, image.revisions.count())

        response = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id(), 'r': 'C'}),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "success unread", "Image uploaded")
        revision = self._get_last_image_revision()
        self.assertEqual(1, ImageRevision.objects.filter(image=image).count())
        image = Image.objects.get(pk=image.pk)
        self.assertEqual(1, image.revisions.count())
        self.assertEqual('C', revision.label)

        revision.delete()
        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_edit_make_final_view(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        response = self.client.get(
            reverse('image_edit_make_final', kwargs={'id': image.get_id()}),
            follow=True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        image = self._get_last_image()
        revision = self._get_last_image_revision()
        self.assertEqual(image.is_final, True)
        self.assertEqual(image.revisions.all()[0].is_final, False)
        revision.delete()
        self.client.logout()

        # Test with wrong user
        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_edit_make_final', kwargs={'id': image.get_id()}))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_edit_revision_make_final_view(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')

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
            reverse('image_edit_revision_make_final', kwargs={'id': b.id}),
            follow=True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id(), 'r': b.label}),
            status_code=302,
            target_status_code=200)

        # Check that B is now final
        image = self._get_last_image()
        c = image.revisions.order_by('-label')[0]
        b = image.revisions.order_by('-label')[1]
        self.assertEqual(image.is_final, False)
        self.assertEqual(c.is_final, False)
        self.assertEqual(b.is_final, True)
        c.delete()
        self.client.logout()

        # Test with wrong user
        self.client.login(username='test2', password='password')
        response = self.client.get(
            reverse('image_edit_revision_make_final', kwargs={'id': b.id}))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        b.delete()
        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_edit_basic_view(self, retrieve_primary_thumbnails):
        def post_data(image):
            return {
                'title': "Test title",
                'link': "http://www.example.com",
                'link_to_fits': "http://www.example.com/fits",
                'acquisition_type': 'EAA',
                'data_source': 'OTHER',
                'subject_type': SubjectType.OTHER,
                'locations': [x.pk for x in image.user.userprofile.location_set.all()],
                'description': "Image description",
                'allow_comments': True
            }

        def get_url(args=None):
            return reverse('image_edit_basic', args=args)

        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.subject_type = SubjectType.DEEP_SKY
        image.save(keep_deleted=True)
        self.client.logout()

        # GET
        self.client.login(username='test2', password='password')
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 403)

        # POST
        response = self.client.post(get_url((image.get_id(),)), post_data(image), follow=True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # GET
        self.client.login(username='test', password='password')
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 200)

        # POST
        location, created = Location.objects.get_or_create(
            name="Test location")
        self.user.userprofile.location_set.add(location)
        response = self.client.post(get_url((image.get_id(),)), post_data(image), follow=True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        image = Image.objects_including_wip.get(pk=image.pk)
        self.assertEqual(image.title, "Test title")
        self.assertEqual(image.link, "http://www.example.com")
        self.assertEqual(image.link_to_fits, "http://www.example.com/fits")
        self.assertEqual(image.acquisition_type, 'EAA')
        self.assertEqual(image.subject_type, SubjectType.OTHER)
        self.assertEqual(image.solar_system_main_subject, None)
        self.assertEqual(image.locations.count(), 1)
        self.assertEqual(image.locations.all().first().pk, image.user.userprofile.location_set.all().first().pk)
        self.assertEqual(image.description, "Image description")
        self.assertEqual(image.allow_comments, True)

        # Test that groups are updated
        group1 = AstroBinGroup.objects.create(
            name="group1", creator=self.user, owner=self.user,
            category=100)
        group2 = AstroBinGroup.objects.create(
            name="group2", creator=self.user, owner=self.user,
            category=100)
        group3 = AstroBinGroup.objects.create(
            name="group3", creator=self.user, owner=self.user,
            category=100, autosubmission=True)

        response = self.client.get(get_url((image.get_id(),)))
        self.assertContains(response, "group1")
        self.assertContains(response, "group2")
        self.assertNotContains(response, "group3")

        response = self.client.get(image.get_absolute_url())
        self.assertContains(response, "Acquisition type")
        self.assertContains(response, "Electronically-Assisted Astronomy (EAA)")

        data = post_data(image)

        data.update({"groups": [group1.pk]})
        response = self.client.post(get_url((image.get_id(),)), data, follow=True)
        image = Image.objects_including_wip.get(pk=image.pk)
        self.assertTrue(group1 in image.part_of_group_set.all())
        self.assertFalse(group2 in image.part_of_group_set.all())

        data.update({"groups": [group1.pk, group2.pk]})
        response = self.client.post(get_url((image.get_id(),)), data, follow=True)
        image = Image.objects_including_wip.get(pk=image.pk)
        self.assertTrue(group1 in image.part_of_group_set.all())
        self.assertTrue(group2 in image.part_of_group_set.all())

        data.update({"groups": [group2.pk]})
        response = self.client.post(get_url((image.get_id(),)), data, follow=True)
        image = Image.objects_including_wip.get(pk=image.pk)
        self.assertFalse(group1 in image.part_of_group_set.all())
        self.assertTrue(group2 in image.part_of_group_set.all())

        data.update({"groups": []})
        response = self.client.post(get_url((image.get_id(),)), data, follow=True)
        image = Image.objects_including_wip.get(pk=image.pk)
        self.assertFalse(group1 in image.part_of_group_set.all())
        self.assertFalse(group2 in image.part_of_group_set.all())

        group1.delete()
        group2.delete()
        group3.delete()

        # Invalid form
        response = self.client.post(get_url((image.get_id(),)), {})
        self.assertContains(response, "This field is required");
        self.client.logout()

        # Anonymous GET
        response = self.client.get(get_url((image.get_id(),)))
        self.assertRedirects(
            response,
            '/accounts/login/?next=' + get_url((image.get_id(),)),
            status_code=302,
            target_status_code=200)

        # Anonymous POST
        response = self.client.post(get_url((image.get_id(),)), post_data(image), follow=True)
        self.assertRedirects(
            response,
            '/accounts/login/?next=' + get_url((image.get_id(),)),
            status_code=302,
            target_status_code=200)

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_edit_basic_view_replacing_image_deletes_solution(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')

        image = self._get_last_image()
        Solution.objects.create(
            status=Solver.SUCCESS,
            content_object=image
        )

        data = {
            'image_file': open('astrobin/fixtures/test.jpg', 'rb'),
            'title': "Test title",
            'link': "http://www.example.com",
            'link_to_fits': "http://www.example.com/fits",
            'acquisition_type': 'EAA',
            'data_source': 'OTHER',
            'subject_type': SubjectType.OTHER,
            'locations': [],
            'description': "Image description",
            'allow_comments': True
        }

        self.assertIsNotNone(image.solution)

        self.client.post(reverse('image_edit_basic', args=(image.get_id(),)), data, follow=True)
        self.assertIsNone(image.solution)

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_edit_watermark_view(self, retrieve_primary_thumbnails):
        def post_data(image):
            return {
                'image_id': image.get_id(),
                'watermark': True,
                'watermark_text': "Watermark test",
                'watermark_position': 0,
                'watermark_size': 'S',
                'watermark_opacity': 100
            }

        def get_url(args=None):
            return reverse('image_edit_watermark', args=args)

        def post_url(args=None):
            return reverse('image_edit_save_watermark', args=args)

        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.title = "Test title"
        image.save(keep_deleted=True)
        self.client.logout()

        # GET
        self.client.login(username='test2', password='password')
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 403)

        # POST
        response = self.client.post(
            post_url(),
            post_data(image),
            follow=True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # GET
        self.client.login(username='test', password='password')
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 200)

        # POST
        response = self.client.post(
            post_url(),
            post_data(image),
            follow=True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        image = Image.objects.get(pk=image.pk)
        self.assertEqual(image.watermark, True)
        self.assertEqual(image.watermark_text, "Watermark test")
        self.assertEqual(image.watermark_position, 0)
        self.assertEqual(image.watermark_size, 'S')
        self.assertEqual(image.watermark_opacity, 100)

        # Missing image_id in post
        response = self.client.post(post_url(), {})
        self.assertEqual(response.status_code, 404)

        # Invalid form
        response = self.client.post(post_url(), {'image_id': image.get_id()})
        self.assertEqual(response.status_code, 200)
        self._assert_message(response, "error unread", "errors processing the form")
        self.client.logout()

        # Anonymous GET
        response = self.client.get(get_url((image.get_id(),)))
        self.assertRedirects(
            response,
            '/accounts/login/?next=' +
            get_url((image.get_id(),)),
            status_code=302,
            target_status_code=200)

        # Anonymous POST
        response = self.client.post(
            post_url(),
            post_data(image),
            follow=True)
        self.assertRedirects(
            response,
            '/accounts/login/?next=' + post_url(),
            status_code=302,
            target_status_code=200)

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_edit_gear_view(self, retrieve_primary_thumbnails):
        def post_data(image):
            return {
                'image_id': image.get_id(),
                'imaging_telescopes': ','.join(["%d" % x.pk for x in self.imaging_telescopes]),
                'guiding_telescopes': ','.join(["%d" % x.pk for x in self.guiding_telescopes]),
                'mounts': ','.join(["%d" % x.pk for x in self.mounts]),
                'imaging_cameras': ','.join(["%d" % x.pk for x in self.imaging_cameras]),
                'guiding_cameras': ','.join(["%d" % x.pk for x in self.guiding_cameras]),
                'focal_reducers': ','.join(["%d" % x.pk for x in self.focal_reducers]),
                'software': ','.join(["%d" % x.pk for x in self.software]),
                'filters': ','.join(["%d" % x.pk for x in self.filters]),
                'accessories': ','.join(["%d" % x.pk for x in self.accessories])
            }

        def get_url(args=None):
            return reverse('image_edit_gear', args=args)

        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.title = "Test title"
        image.save(keep_deleted=True)
        self.client.logout()

        # GET
        self.client.login(username='test2', password='password')
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 403)

        # POST
        response = self.client.post(
            get_url((image.get_id(),)),
            post_data(image),
            follow=True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # GET
        self.client.login(username='test', password='password')
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 200)

        # No gear
        self.user.userprofile.telescopes.clear()
        self.user.userprofile.cameras.clear()

        response = self.client.get(get_url((image.get_id(),)))
        self.assertContains(response, "Can't see anything here?")

        self.user.userprofile.telescopes = self.imaging_telescopes + self.guiding_telescopes
        self.user.userprofile.cameras = self.imaging_cameras + self.guiding_cameras

        # Check that the user's other images are available to copy from
        self._do_upload('astrobin/fixtures/test.jpg')
        other_1 = self._get_last_image();
        other_1.title = "Other 1";
        other_1.save(keep_deleted=True)
        self._do_upload('astrobin/fixtures/test.jpg', wip=True);
        other_2 = self._get_last_image();
        other_2.title = "Other 2";
        other_2.save(keep_deleted=True)
        response = self.client.get(get_url((image.get_id(),)))
        other_images = Image.objects_including_wip \
            .filter(user=self.user) \
            .exclude(pk=image.pk)
        for i in other_images:
            self.assertContains(
                response,
                '<option value="%d">%s</option>' % (i.pk, i.title),
                html=True)
        other_1.delete()
        other_2.delete()

        # POST
        response = self.client.post(
            get_url((image.get_id(),)),
            post_data(image),
            follow=True)
        self.assertEqual(response.status_code, 200)
        self._assert_message(response, "success unread", "Form saved")
        image = Image.objects.get(pk=image.pk)
        self.assertEqual(list(image.imaging_telescopes.all()), self.imaging_telescopes)
        self.assertEqual(list(image.guiding_telescopes.all()), self.guiding_telescopes)
        self.assertEqual(list(image.mounts.all()), self.mounts)
        self.assertEqual(list(image.imaging_cameras.all()), self.imaging_cameras)
        self.assertEqual(list(image.guiding_cameras.all()), self.guiding_cameras)
        self.assertEqual(list(image.focal_reducers.all()), self.focal_reducers)
        self.assertEqual(list(image.software.all()), self.software)
        self.assertEqual(list(image.filters.all()), self.filters)
        self.assertEqual(list(image.accessories.all()), self.accessories)

        # No data
        response = self.client.post(get_url((image.get_id(),)), {}, follow=True)
        self.assertRedirects(response, reverse('image_detail', args=(image.get_id(),)))
        self.client.logout()

        # Anonymous GET
        response = self.client.get(get_url((image.get_id(),)))
        self.assertRedirects(
            response,
            '/accounts/login/?next=' +
            get_url((image.get_id(),)),
            status_code=302,
            target_status_code=200)

        # Anonymous POST
        response = self.client.post(
            get_url((image.get_id(),)),
            post_data(image),
            follow=True)
        self.assertRedirects(
            response,
            '/accounts/login/?next=' + get_url((image.get_id(),)),
            status_code=302,
            target_status_code=200)

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_edit_acquisition_view(self, retrieve_primary_thumbnails):
        today = time.strftime('%Y-%m-%d')

        def post_data_deep_sky_simple(image):
            return {
                'image_id': image.get_id(),
                'edit_type': 'deep_sky',
                'advanced': 'false',
                'date': today,
                'number': 10,
                'duration': 1200,
            }

        def post_data_deep_sky_advanced(image):
            return {
                'deepsky_acquisition_set-TOTAL_FORMS': 1,
                'deepsky_acquisition_set-INITIAL_FORMS': 0,
                'image_id': image.get_id(),
                'edit_type': 'deep_sky',
                'advanced': 'true',
                'deepsky_acquisition_set-0-date': today,
                'deepsky_acquisition_set-0-number': 10,
                'deepsky_acquisition_set-0-duration': 1200,
                'deepsky_acquisition_set-0-binning': 1,
                'deepsky_acquisition_set-0-iso': 3200,
                'deepsky_acquisition_set-0-gain': 1,
                'deepsky_acquisition_set-0-sensor_cooling': -20,
                'deepsky_acquisition_set-0-darks': 10,
                'deepsky_acquisition_set-0-flats': 10,
                'deepsky_acquisition_set-0-flat_darks': 10,
                'deepsky_acquisition_set-0-bias': 0,
                'deepsky_acquisition_set-0-bortle': 1,
                'deepsky_acquisition_set-0-mean_sqm': 20.0,
                'deepsky_acquisition_set-0-mean_fwhm': 1,
                'deepsky_acquisition_set-0-temperature': 10
            }

        def post_data_solar_system(image):
            return {
                'image_id': image.get_id(),
                'edit_type': 'solar_system',
                'date': today,
                'frames': 1000,
                'fps': 100,
                'focal_length': 5000,
                'cmi': 1.0,
                'cmii': 2.0,
                'cmiii': 3.0,
                'seeing': 1,
                'transparency': 1,
                'time': "00:00"
            }

        def get_url(args=None):
            return reverse('image_edit_acquisition', args=args)

        def post_url(args=None):
            return reverse('image_edit_save_acquisition', args=args)

        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.title = "Test title"
        image.save(keep_deleted=True)
        self.client.logout()

        # GET with wrong user
        self.client.login(username='test2', password='password')
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 403)

        # POST with wrong user
        response = self.client.post(
            post_url(),
            post_data_deep_sky_simple(image),
            follow=True)
        self.assertEqual(response.status_code, 403)

        # Reset with wrong user
        response = self.client.get(
            reverse('image_edit_acquisition_reset', args=(image.get_id(),)))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # GET
        self.client.login(username='test', password='password')
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 200)

        # GET with existing DSA
        dsa, created = DeepSky_Acquisition.objects.get_or_create(
            image=image,
            date=today)
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 200)

        # GET with existing DSA in advanced mode
        dsa.advanced = True
        dsa.save()
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 200)

        # Test the add_more argument for the formset
        response = self.client.get(get_url((image.get_id(),)) + "?add_more")
        self.assertEqual(response.status_code, 200)
        dsa.delete()

        # GET with existing SSA
        ssa, created = SolarSystem_Acquisition.objects.get_or_create(
            image=image,
            date=today)
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 200)
        ssa.delete()

        # GET with edit_type in request.GET
        response = self.client.get(get_url((image.get_id(),)) + "?edit_type=deep_sky")
        self.assertEqual(response.status_code, 200)

        # Reset
        response = self.client.get(
            reverse('image_edit_acquisition_reset', args=(image.get_id(),)))
        self.assertEqual(response.status_code, 200)

        # POST basic deep sky
        response = self.client.post(
            post_url(),
            post_data_deep_sky_simple(image),
            follow=True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self.assertEquals(image.acquisition_set.count(), 1)
        dsa = DeepSky_Acquisition.objects.filter(image=image)[0]
        post_data = post_data_deep_sky_simple(image)
        self.assertEqual(dsa.date.strftime("%Y-%m-%d"), post_data['date'])
        self.assertEqual(dsa.number, post_data['number'])
        self.assertEqual(dsa.duration, post_data['duration'])
        dsa.delete()

        # POST basic deep sky invalid form
        post_data = post_data_deep_sky_simple(image)
        post_data['number'] = "foo"
        response = self.client.post(post_url(), post_data)
        self.assertEqual(response.status_code, 200)
        self._assert_message(response, "error unread", "errors processing the form")
        self.assertEquals(image.acquisition_set.count(), 0)

        # POST advanced deep sky
        response = self.client.post(
            post_url(),
            post_data_deep_sky_advanced(image),
            follow=True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self.assertEquals(image.acquisition_set.count(), 1)
        dsa = DeepSky_Acquisition.objects.filter(image=image)[0]
        post_data = post_data_deep_sky_advanced(image)
        self.assertEqual(dsa.date.strftime("%Y-%m-%d"), post_data['deepsky_acquisition_set-0-date'])
        self.assertEqual(dsa.number, post_data['deepsky_acquisition_set-0-number'])
        self.assertEqual(dsa.duration, post_data['deepsky_acquisition_set-0-duration'])
        self.assertEqual(dsa.binning, post_data['deepsky_acquisition_set-0-binning'])
        self.assertEqual(dsa.iso, post_data['deepsky_acquisition_set-0-iso'])
        self.assertEqual(dsa.gain, post_data['deepsky_acquisition_set-0-gain'])
        self.assertEqual(dsa.sensor_cooling, post_data['deepsky_acquisition_set-0-sensor_cooling'])
        self.assertEqual(dsa.darks, post_data['deepsky_acquisition_set-0-darks'])
        self.assertEqual(dsa.flats, post_data['deepsky_acquisition_set-0-flats'])
        self.assertEqual(dsa.flat_darks, post_data['deepsky_acquisition_set-0-flat_darks'])
        self.assertEqual(dsa.bias, post_data['deepsky_acquisition_set-0-bias'])
        self.assertEqual(dsa.bortle, post_data['deepsky_acquisition_set-0-bortle'])
        self.assertEqual(dsa.mean_sqm, post_data['deepsky_acquisition_set-0-mean_sqm'])
        self.assertEqual(dsa.mean_fwhm, post_data['deepsky_acquisition_set-0-mean_fwhm'])
        self.assertEqual(dsa.temperature, post_data['deepsky_acquisition_set-0-temperature'])
        dsa.delete()

        # POST advanced deep sky with "add_mode"
        post_data = post_data_deep_sky_advanced(image)
        post_data['add_more'] = True
        response = self.client.post(post_url(), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(image.acquisition_set.count(), 1)
        image.acquisition_set.all().delete()

        # POST advanced deep sky invalid form
        post_data = post_data_deep_sky_advanced(image)
        post_data['deepsky_acquisition_set-0-number'] = "foo"
        response = self.client.post(post_url(), post_data)
        self.assertEqual(response.status_code, 200)
        self._assert_message(response, "error unread", "errors processing the form")
        self.assertEquals(image.acquisition_set.count(), 0)

        # POST with missing image_id
        response = self.client.post(post_url(), {}, follow=True)
        self.assertEqual(response.status_code, 404)

        # POST with invalid SSA from
        post_data = post_data_solar_system(image)
        post_data['frames'] = "foo"
        response = self.client.post(post_url(), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._assert_message(response, "error unread", "errors processing the form")
        self.assertEquals(image.acquisition_set.count(), 0)

        # POST with existing SSA
        ssa, created = SolarSystem_Acquisition.objects.get_or_create(
            image=image,
            date=today)
        response = self.client.post(
            post_url(), post_data_solar_system(image), follow=True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self.assertEquals(image.acquisition_set.count(), 1)
        ssa = SolarSystem_Acquisition.objects.filter(image=image)[0]
        post_data = post_data_solar_system(image)
        self.assertEqual(ssa.date.strftime("%Y-%m-%d"), post_data['date'])
        self.assertEqual(ssa.frames, post_data['frames'])
        self.assertEqual(ssa.fps, post_data['fps'])
        self.assertEqual(ssa.focal_length, post_data['focal_length'])
        self.assertEqual(ssa.cmi, post_data['cmi'])
        self.assertEqual(ssa.cmii, post_data['cmii'])
        self.assertEqual(ssa.cmiii, post_data['cmiii'])
        self.assertEqual(ssa.seeing, post_data['seeing'])
        self.assertEqual(ssa.transparency, post_data['transparency'])
        self.assertEqual(ssa.time, post_data['time'])

        self.client.logout()
        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_edit_license_view(self, retrieve_primary_thumbnails):
        def post_data(image):
            return {
                'image_id': image.get_id(),
                'license': 1,
            }

        def get_url(args=None):
            return reverse('image_edit_license', args=args)

        def post_url(args=None):
            return reverse('image_edit_save_license', args=args)

        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.title = "Test title"
        image.save(keep_deleted=True)
        self.client.logout()

        # GET with wrong user
        self.client.login(username='test2', password='password')
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 403)

        # POST with wrong user
        response = self.client.post(post_url(), post_data(image))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # GET
        self.client.login(username='test', password='password')
        response = self.client.get(get_url((image.get_id(),)))
        self.assertEqual(response.status_code, 200)

        # POST with missing image_id
        response = self.client.post(post_url(), {})
        self.assertEqual(response.status_code, 404)

        # POST invalid form
        data = post_data(image)
        data['license'] = "foo"
        response = self.client.post(post_url(), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._assert_message(response, "error unread", "errors processing the form")

        # POST
        response = self.client.post(post_url(), post_data(image), follow=True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "success unread", "Form saved")
        image = Image.objects.get(pk=image.pk)
        self.assertEquals(image.license, 1)

        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_edit_revision_view(self, retrieve_primary_thumbnails):
        def post_data():
            return {
                'description': "Updated revision description",
            }

        def get_url(args=None):
            return reverse('image_edit_revision', args=args)

        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.title = "Test title"
        image.save(keep_deleted=True)
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg', "Test revision description")
        revision = self._get_last_image_revision()
        self.client.logout()

        # GET with wrong user
        self.client.login(username='test2', password='password')
        response = self.client.get(get_url((revision.pk,)))
        self.assertEqual(response.status_code, 403)

        # POST with wrong user
        response = self.client.post(get_url((revision.pk,)), post_data())
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # GET missing revision
        self.client.login(username='test', password='password')
        response = self.client.get(get_url((999,)))
        self.assertEqual(response.status_code, 404)

        # GET
        self.client.login(username='test', password='password')
        response = self.client.get(get_url((revision.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test revision description")

        # POST
        response = self.client.post(get_url((revision.pk,)), post_data(), follow=True)
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id(), 'r': revision.label}),
            status_code=302,
            target_status_code=200)
        self._assert_message(response, "success unread", "Form saved")
        revision = ImageRevision.objects.get(pk=revision.pk)
        self.assertEquals(revision.description, "Updated revision description")

        self.client.logout()

    def test_image_delete_has_permanently_deleted_text(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        response = self.client.get(reverse('image_detail', args=(image.get_id(),)))

        self.assertContains(response, "The image will be permanently")

    def test_image_delete_has_permanently_deleted_text_premium(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        Generators.premium_subscription(image.user, "AstroBin Premium 2020+")

        response = self.client.get(reverse('image_detail', args=(image.get_id(),)))

        self.assertContains(response, "The image will be permanently")

    def test_image_delete_has_trash_text_ultimate(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        Generators.premium_subscription(image.user, "AstroBin Ultimate 2020+")

        response = self.client.get(reverse('image_detail', args=(image.get_id(),)))

        self.assertContains(response, "The image will be moved to the trash")

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_delete_view(self, retrieve_primary_thumbnails):
        def post_url(args=None):
            return reverse('image_delete', args=args)

        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self.client.logout()

        # Try with anonymous user
        response = self.client.post(post_url((image.get_id(),)))
        self.assertRedirects(
            response,
            '/accounts/login/?next=' + post_url((image.get_id(),)),
            status_code=302,
            target_status_code=200)

        # POST with wrong user
        self.client.login(username='test2', password='password')
        response = self.client.post(post_url((image.get_id(),)))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Test deleting WIP image
        self.client.login(username='test', password='password')
        image.is_wip = True
        image.save(keep_deleted=True)
        response = self.client.post(post_url((image.get_id(),)))
        self.assertRedirects(
            response,
            reverse('user_page', kwargs={'username': image.user.username}),
            status_code=302,
            target_status_code=200)
        self.assertEquals(Image.objects_including_wip.filter(pk=image.pk).count(), 0)

        # Test for success
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        response = self.client.post(post_url((image.get_id(),)))
        self.assertRedirects(
            response,
            reverse('user_page', kwargs={'username': image.user.username}),
            status_code=302,
            target_status_code=200)
        self.assertEquals(Image.objects_including_wip.filter(pk=image.pk).count(), 0)
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_delete_revision_view(self, retrieve_primary_thumbnails):
        def post_url(args=None):
            return reverse('image_delete_revision', args=args)

        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()
        self.client.logout()

        # Try with anonymous user
        response = self.client.post(post_url((revision.pk,)))
        self.assertRedirects(
            response,
            '/accounts/login/?next=' + post_url((revision.pk,)),
            status_code=302,
            target_status_code=200)

        # POST with wrong user
        self.client.login(username='test2', password='password')
        response = self.client.post(post_url((revision.pk,)))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Test for success
        self.client.login(username='test', password='password')
        response = self.client.post(post_url((revision.pk,)))
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self.assertEquals(ImageRevision.objects.filter(pk=revision.pk).count(), 0)
        self.assertTrue(image.is_final)
        self.assertFalse(ImageRevision.deleted_objects.get(pk=revision.pk).is_final)
        self.client.logout()

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_delete_original_view(self, retrieve_primary_thumbnails):
        def post_url(args=None):
            return reverse('image_delete_original', args=args)

        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self.client.logout()

        # POST with wrong user
        self.client.login(username='test2', password='password')
        response = self.client.post(post_url((image.get_id(),)))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Test when there are no revisions
        self.client.login(username='test', password='password')
        response = self.client.post(post_url((image.get_id(),)))
        self.assertEquals(400, response.status_code)
        self.assertEquals(Image.objects.filter(pk=image.pk).count(), 1)

        # Test for success when image was not final
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()
        response = self.client.post(post_url((image.get_id(),)))
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self.assertEquals(ImageRevision.objects.filter(image=image).count(), 0)
        image.delete()

        # Test for success when image was final
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()
        image = Image.objects.get(pk=image.pk)
        image.is_final = True
        image.save(keep_deleted=True)
        revision.is_final = False
        revision.save(keep_deleted=True)

        response = self.client.post(post_url((image.get_id(),)))
        self.assertRedirects(
            response,
            reverse('image_detail', kwargs={'id': image.get_id()}),
            status_code=302,
            target_status_code=200)
        self.assertEquals(ImageRevision.objects.filter(image=image).count(), 0)
        image.delete()

        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_promote_view(self, retrieve_primary_thumbnails):
        def post_url(args=None):
            return reverse('image_promote', args=args)

        # Upload a WIP image and a public image
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        public_image = self._get_last_image()

        self._do_upload('astrobin/fixtures/test.jpg', True)
        wip_image = self._get_last_image()

        # user2 follows user
        self.client.logout()
        self.client.login(username='test2', password='password')
        response = self.client.post(
            reverse('toggleproperty_ajax_add'),
            {
                'property_type': 'follow',
                'object_id': self.user.pk,
                'content_type_id': ContentType.objects.get_for_model(User).pk,
            })
        self.assertEqual(response.status_code, 200)

        # GET with wrong user
        response = self.client.post(post_url((public_image.get_id(),)))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Test public image
        self.client.login(username='test', password='password')
        response = self.client.post(post_url((public_image.get_id(),)))
        image = Image.objects.get(pk=public_image.pk)
        self.assertEquals(image.is_wip, False)
        self.assertEquals(len(get_unseen_notifications(self.user2)), 0)

        # Test WIP image
        self.assertIsNone(wip_image.published)
        self.assertTrue(wip_image.is_wip)
        response = self.client.post(post_url((wip_image.get_id(),)))
        wip_image = Image.objects.get(pk=wip_image.pk)
        self.assertFalse(wip_image.is_wip)
        self.assertIsNotNone(wip_image.published)
        notifications = get_unseen_notifications(self.user2)
        self.assertEquals(len(notifications), 1)
        self.assertTrue("a new image" in notifications[0].message)

        # Test that previously published images don't trigger a notification
        wip_image.is_wip = True
        wip_image.save(keep_deleted=True)
        response = self.client.post(post_url((wip_image.get_id(),)))
        wip_image = Image.objects.get(pk=wip_image.pk)
        self.assertFalse(wip_image.is_wip)
        self.assertIsNotNone(wip_image.published)
        self.assertEquals(len(get_unseen_notifications(self.user2)), 1)  # Same as before

        image.delete()

        # Test the `published` property
        self._do_upload('astrobin/fixtures/test.jpg', True)
        image = self._get_last_image()
        self.assertTrue(image.is_wip)
        self.assertIsNone(image.published)
        response = self.client.post(post_url((image.get_id(),)))
        image = Image.objects.get(pk=image.pk)
        self.assertIsNotNone(image.published)

        # The `published` field does not get updated the second time we make
        # this image public.
        published = image.published
        image.is_wip = True
        image.save(keep_deleted=True)
        response = self.client.post(post_url((image.get_id(),)))
        image = Image.objects.get(pk=image.pk)
        self.assertEqual(published, image.published)

        image.delete()

        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_demote_view(self, retrieve_primary_thumbnails):
        def post_url(args=None):
            return reverse('image_demote', args=args)

        # Upload an image
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        # GET with wrong user
        self.client.logout()
        self.client.login(username='test2', password='password')
        response = self.client.post(post_url((image.get_id(),)))
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.client.login(username='test', password='password')

        # Test when image was not WIP
        response = self.client.post(post_url((image.get_id(),)))
        image = Image.objects_including_wip.get(pk=image.pk)
        self.assertEquals(image.is_wip, True)

        # Test when image was WIP
        response = self.client.post(post_url((image.get_id(),)))
        image = Image.objects_including_wip.get(pk=image.pk)
        self.assertEquals(image.is_wip, True)

        # Test that we can't get the image via the regular manager
        self.assertEquals(Image.objects.filter(pk=image.pk).count(), 0)

        self.client.logout()
        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_moderation(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.title = "TEST IMAGE"
        image.save(keep_deleted=True)

        # As the test user does not have a high enough AstroBin Index, the
        # iamge should be in the moderation queue.
        self.assertEquals(image.moderator_decision, 0)
        self.assertEquals(image.moderated_when, None)
        self.assertEquals(image.moderated_by, None)

        # The image should not appear on the front page when logged out
        self.client.logout()
        response = self.client.get(reverse('index'))
        self.assertEquals(image.title in response.content, False)

        # Nor when logged in
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('index'))
        self.assertEquals(image.title in response.content, False)

        # TODO: test image promotion

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_updated_after_toggleproperty(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.title = "TEST IMAGE"
        image.save(keep_deleted=True)

        updated = image.updated

        prop = ToggleProperty.objects.create_toggleproperty('like', image, self.user2)
        image = self._get_last_image()
        self.assertNotEquals(updated, image.updated)

        updated = image.updated
        prop = ToggleProperty.objects.create_toggleproperty('bookmark', image, self.user2)
        image = self._get_last_image()
        self.assertNotEquals(updated, image.updated)

        updated = image.updated
        prop.delete()
        image = self._get_last_image()
        self.assertNotEquals(updated, image.updated)

        image.delete()
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_updated_after_acquisition_saved(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.title = "TEST IMAGE"
        image.save(keep_deleted=True)

        updated = image.updated

        today = time.strftime('%Y-%m-%d')
        response = self.client.post(
            reverse('image_edit_save_acquisition'),
            {
                'image_id': image.get_id(),
                'edit_type': 'deep_sky',
                'advanced': 'false',
                'date': today,
                'number': 10,
                'duration': 1200
            },
            follow=True)

        image = self._get_last_image()
        self.assertNotEquals(updated, image.updated)

        image.delete()
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_updated_after_comment(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.title = "TEST IMAGE"
        image.save(keep_deleted=True)

        updated = image.updated

        comment = NestedComment.objects.create(
            content_object=image,
            author=self.user2,
            text="Test")

        image = self._get_last_image()
        self.assertNotEquals(updated, image.updated)

        image.delete()
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_softdelete(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        image.delete()
        self.assertFalse(Image.objects.filter(pk=image.pk).exists())
        self.assertTrue(Image.all_objects.filter(pk=image.pk).exists())

        image.undelete()
        self.assertTrue(Image.objects.filter(pk=image.pk).exists())

        self._do_upload_revision(image, 'astrobin/fixtures/test_smaller.jpg')
        revision = self._get_last_image_revision()

        image = Image.objects.get(pk=image.pk)
        self.assertEquals(1, image.revisions.count())

        revision.delete()
        with self.assertRaises(ImageRevision.DoesNotExist):
            revision = ImageRevision.objects.get(pk=revision.pk)
        image = Image.objects.get(pk=image.pk)
        self.assertEquals(0, image.revisions.count())
        self.assertFalse(ImageRevision.objects.filter(pk=revision.pk).exists())
        self.assertTrue(ImageRevision.all_objects.filter(pk=revision.pk).exists())

    def test_image_corrupted_goes_to_404_if_anon(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()
        image.corrupted = True
        image.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertEquals(404, response.status_code)

    def test_image_corrupted_goes_to_404_if_anon_and_r0(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()
        image.corrupted = True
        image.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': '0'}), follow=True)
        self.assertEquals(404, response.status_code)

    def test_image_corrupted_goes_to_edit_if_owner(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')

        image = self._get_last_image()
        image.corrupted = True
        image.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}), follow=True)
        self.assertRedirects(response, reverse('image_edit_basic', kwargs={'id': image.get_id()}) + '?corrupted')

    def test_image_corrupted_goes_to_edit_if_owner_and_r0(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')

        image = self._get_last_image()
        image.corrupted = True
        image.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': '0'}), follow=True)
        self.assertRedirects(response, reverse('image_edit_basic', kwargs={'id': image.get_id()}) + '?corrupted')

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_revision_corrupted_goes_to_404_if_anon(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        revision.corrupted = True
        revision.save()

        self.client.logout()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': revision.label}))
        self.assertEquals(404, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_revision_corrupted_ok_if_anon_and_r0(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        revision.corrupted = True
        revision.save()

        self.client.logout()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': '0'}))
        self.assertEquals(200, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_revision_corrupted_ok_if_owner_and_r0(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        revision.corrupted = True
        revision.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': '0'}))
        self.assertEquals(200, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_revision_corrupted_goes_to_edit_revision_if_owner(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        revision.corrupted = True
        revision.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': revision.label}))
        self.assertRedirects(response, reverse('image_edit_revision', kwargs={'id': revision.pk}) + '?corrupted')

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_corrupted_ok_if_final_revision(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.corrupted = True
        image.save()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        self.client.logout()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}), follow=True)
        self.assertEquals(200, response.status_code)

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': revision.label}))
        self.assertEquals(200, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_corrupted_404_if_non_final_revision_and_anon(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        image.corrupted = True
        image.is_final = True
        image.save()

        revision.is_final = False
        revision.save()

        self.client.logout()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}), follow=True)
        self.assertEquals(404, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_corrupted_goes_to_edit_if_non_final_revision_and_owner(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        image.corrupted = True
        image.is_final = True
        image.save()

        revision.is_final = False
        revision.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}), follow=True)
        self.assertRedirects(response, reverse('image_edit_basic', kwargs={'id': image.get_id()}) + '?corrupted')

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_corrupted_ok_if_non_final_revision_direct_link_and_anon(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        image.corrupted = True
        image.is_final = True
        image.save()

        revision.is_final = False
        revision.save()

        self.client.logout()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id(), 'r': revision.label}))
        self.assertEquals(200, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_corrupted_ok_if_non_final_revision_direct_link_and_owner(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        image.corrupted = True
        image.is_final = True
        image.save()

        revision.is_final = False
        revision.save()

        response = self.client.get(
            reverse('image_detail', kwargs={'id': image.get_id(), 'r': revision.label}))
        self.assertEquals(200, response.status_code)

    #

    def test_image_full_corrupted_goes_to_404_if_anon(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()
        image.corrupted = True
        image.save()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id()}))
        self.assertEquals(404, response.status_code)

    def test_image_full_corrupted_goes_to_404_if_anon_and_r0(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = self._get_last_image()
        image.corrupted = True
        image.save()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id(), 'r': '0'}), follow=True)
        self.assertEquals(404, response.status_code)

    def test_image_full_corrupted_goes_to_edit_if_owner(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')

        image = self._get_last_image()
        image.corrupted = True
        image.save()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id()}), follow=True)
        self.assertRedirects(response, reverse('image_edit_basic', kwargs={'id': image.get_id()}) + '?corrupted')

    def test_image_full_corrupted_goes_to_edit_if_owner_and_r0(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')

        image = self._get_last_image()
        image.corrupted = True
        image.save()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id(), 'r': '0'}), follow=True)
        self.assertRedirects(response, reverse('image_edit_basic', kwargs={'id': image.get_id()}) + '?corrupted')

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_full_revision_corrupted_goes_to_404_if_anon(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        revision.corrupted = True
        revision.save()

        self.client.logout()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id(), 'r': revision.label}))
        self.assertEquals(404, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_full_revision_corrupted_ok_if_anon_and_r0(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        revision.corrupted = True
        revision.save()

        self.client.logout()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id(), 'r': '0'}))
        self.assertEquals(200, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_full_revision_corrupted_ok_if_owner_and_r0(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        revision.corrupted = True
        revision.save()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id(), 'r': '0'}))
        self.assertEquals(200, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_full_revision_corrupted_goes_to_edit_revision_if_owner(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        revision.corrupted = True
        revision.save()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id(), 'r': revision.label}))
        self.assertRedirects(response, reverse('image_edit_revision', kwargs={'id': revision.pk}) + '?corrupted')

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_full_corrupted_ok_if_final_revision(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.corrupted = True
        image.save()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        self.client.logout()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id()}), follow=True)
        self.assertEquals(200, response.status_code)

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id(), 'r': revision.label}))
        self.assertEquals(200, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_full_corrupted_404_if_non_final_revision_and_anon(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        image.corrupted = True
        image.is_final = True
        image.save()

        revision.is_final = False
        revision.save()

        self.client.logout()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id()}), follow=True)
        self.assertEquals(404, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_full_corrupted_goes_to_edit_if_non_final_revision_and_owner(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        image.corrupted = True
        image.is_final = True
        image.save()

        revision.is_final = False
        revision.save()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id()}), follow=True)
        self.assertRedirects(response, reverse('image_edit_basic', kwargs={'id': image.get_id()}) + '?corrupted')

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_full_corrupted_ok_if_non_final_revision_direct_link_and_anon(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        image.corrupted = True
        image.is_final = True
        image.save()

        revision.is_final = False
        revision.save()

        self.client.logout()

        response = self.client.get(reverse('image_full', kwargs={'id': image.get_id(), 'r': revision.label}))
        self.assertEquals(200, response.status_code)

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_image_full_corrupted_ok_if_non_final_revision_direct_link_and_owner(self):
        self.client.login(username='test', password='password')

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()

        self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision = self._get_last_image_revision()

        image.corrupted = True
        image.is_final = True
        image.save()

        revision.is_final = False
        revision.save()

        response = self.client.get(
            reverse('image_full', kwargs={'id': image.get_id(), 'r': revision.label}))
        self.assertEquals(200, response.status_code)

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_anon_see_ads(self, retrieve_primary_thumbnails):
        image = Generators.image()
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "div class=\"subtle-container advertisement\"")
        image.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_free_see_ads(self, retrieve_primary_thumbnails):
        image = Generators.image()
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "div class=\"subtle-container advertisement\"")
        image.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_free_see_ads_with_allow_ads_as_false(self, retrieve_primary_thumbnails):
        image = Generators.image()
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "div class=\"subtle-container advertisement\"")
        self.client.logout()
        image.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_lite_see_ads(self, retrieve_primary_thumbnails):
        image = Generators.image()
        us = Generators.premium_subscription(self.user, "AstroBin Lite")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "div class=\"subtle-container advertisement\"")
        image.delete()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_lite_dont_see_ads_with_allow_ads_as_false(self, retrieve_primary_thumbnails):
        image = Generators.image()
        us = Generators.premium_subscription(self.user, "AstroBin Lite")
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "div class=\"subtle-container advertisement\"")
        self.client.logout()
        image.delete()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_lite_2020_see_ads(self, retrieve_primary_thumbnails):
        image = Generators.image()
        us = Generators.premium_subscription(self.user, "AstroBin Lite 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "div class=\"subtle-container advertisement\"")
        image.delete()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_lite_2020_see_ads_with_allow_ads_as_false(self, retrieve_primary_thumbnails):
        image = Generators.image()
        us = Generators.premium_subscription(self.user, "AstroBin Lite 2020+")
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "div class=\"subtle-container advertisement\"")
        self.client.logout()
        image.delete()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_premium_see_ads(self, retrieve_primary_thumbnails):
        image = Generators.image()
        us = Generators.premium_subscription(self.user, "AstroBin Premium")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "div class=\"subtle-container advertisement\"")
        image.delete()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_premium_dont_see_ads_with_allow_ads_as_false(self, retrieve_primary_thumbnails):
        image = Generators.image()
        us = Generators.premium_subscription(self.user, "AstroBin Premium")
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "div class=\"subtle-container advertisement\"")
        self.client.logout()
        image.delete()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_premium_2020_see_ads(self, retrieve_primary_thumbnails):
        image = Generators.image()
        us = Generators.premium_subscription(self.user, "AstroBin Premium 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "div class=\"subtle-container advertisement\"")
        image.delete()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_premium_2020_dont_see_ads_with_allow_ads_as_false(self, retrieve_primary_thumbnails):
        image = Generators.image()
        us = Generators.premium_subscription(self.user, "AstroBin Premium 2020+")
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "div class=\"subtle-container advertisement\"")
        self.client.logout()
        image.delete()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_ultimate_2020_see_ads(self, retrieve_primary_thumbnails):
        image = Generators.image()
        us = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "div class=\"subtle-container advertisement\"")
        image.delete()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_ultimate_2020_dont_see_ads_with_allow_ads_as_false(self, retrieve_primary_thumbnails):
        image = Generators.image()
        us = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "div class=\"subtle-container advertisement\"")
        self.client.logout()
        image.delete()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_free_users_dont_see_ads_on_ultimate_2020_images(self, retrieve_primary_thumbnails):
        image = Generators.image()
        image.user = self.user
        image.save()
        us = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "div class=\"subtle-container advertisement\"")

    def test_image_platesolving_not_available_on_free(self):
        image = Generators.image()
        image.user = self.user
        image.subject_type = SubjectType.DEEP_SKY
        image.save()
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "id=\"platesolving-status\"")
        image.delete()

    def test_image_platesolving_available_on_lite(self):
        image = Generators.image()
        image.user = self.user
        image.subject_type = SubjectType.DEEP_SKY
        image.save()
        us = Generators.premium_subscription(self.user, "AstroBin Lite")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "id=\"platesolving-status\"")
        image.delete()

    def test_image_platesolving_available_on_premium(self):
        image = Generators.image()
        image.user = self.user
        image.subject_type = SubjectType.DEEP_SKY
        image.save()
        us = Generators.premium_subscription(self.user, "AstroBin Premium")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "id=\"platesolving-status\"")
        image.delete()

    def test_image_platesolving_available_on_lite_2020(self):
        image = Generators.image()
        image.user = self.user
        image.subject_type = SubjectType.DEEP_SKY
        image.save()
        us = Generators.premium_subscription(self.user, "AstroBin Lite 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "id=\"platesolving-status\"")
        image.delete()

    def test_image_platesolving_available_on_premium_2020(self):
        image = Generators.image()
        image.user = self.user
        image.subject_type = SubjectType.DEEP_SKY
        image.save()
        us = Generators.premium_subscription(self.user, "AstroBin Premium 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "id=\"platesolving-status\"")
        image.delete()

    def test_image_platesolving_available_on_ultimate_2020(self):
        image = Generators.image()
        image.user = self.user
        image.subject_type = SubjectType.DEEP_SKY
        image.save()
        us = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "id=\"platesolving-status\"")
        image.delete()

    def test_image_gear_list_is_hidden(self):
        image = Generators.image()
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "<div class=\"gear\">")
        image.delete()

    def test_image_gear_list_is_shown(self):
        image = Generators.image()
        telescope = Generators.telescope()

        image.imaging_telescopes.add(telescope)
        image.subject_type = SubjectType.DEEP_SKY
        image.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "<div class=\"gear\">")

        telescope.delete()
        image.delete()
