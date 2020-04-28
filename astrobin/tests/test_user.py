import sys
from datetime import date, timedelta, datetime

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.utils import timezone, formats
from django_bouncy.models import Bounce
from mock import patch

from astrobin.enums import SubjectType
from toggleproperties.models import ToggleProperty

from astrobin.models import (
    Acquisition,
    CommercialGear,
    Telescope,
    UserProfile,
    ImageRevision,
    DataDownloadRequest)
from astrobin.tests.generators import Generators
from astrobin_apps_iotd.models import *


class UserTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@example.com",
            password="password")
        self.user_2 = User.objects.create_user(
            username="user_2", email="user_2@example.com",
            password="password")

        self.producers = Group.objects.create(name='Producers')
        self.retailers = Group.objects.create(name='Retailers')
        self.payers = Group.objects.create(name='Paying')

    def tearDown(self):
        self.user.delete()
        self.user_2.delete()
        self.producers.delete()
        self.retailers.delete()
        self.payers.delete()

    def _get_last_image(self):
        return Image.objects_including_wip.all().order_by('-id')[0]

    def _do_upload(self, filename, title="TEST IMAGE", wip=False):
        data = {'image_file': open(filename, 'rb')}
        if wip:
            data['wip'] = True

        patch('astrobin.tasks.retrieve_primary_thumbnails.delay')
        self.client.post(
            reverse('image_upload_process'),
            data,
            follow=True)

        image = self._get_last_image()
        if title:
            image.title = title
            image.save(keep_deleted=True)

        return image

    def _get_last_image_revision(self):
        return ImageRevision.objects.all().order_by('-id')[0]

    def _do_upload_revision(self, image, filename, description=None):
        self.client.post(
            reverse('image_revision_upload_process'),
            {
                'image_id': image.get_id(),
                'image_file': open(filename, 'rb'),
                'description': description,
                'mark_as_final': u'on'
            },
            follow=True)

        revision = self._get_last_image_revision()

        return revision

    def test_user_page_view_anon_cannot_access_trash(self):
        response = self.client.get(reverse('user_page', args=('user',)) + '?trash')
        self.assertEquals(response.status_code, 403)

    def test_user_page_view_cannot_access_another_users_trash(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.client.login(username="user", password="password")
        response = self.client.get(reverse('user_page', args=('user_2',)) + '?trash')
        self.assertEquals(response.status_code, 403)

    def test_user_page_view_free_cannot_access_trash(self):
        self.client.login(username="user", password="password")
        response = self.client.get(reverse('user_page', args=('user',)) + '?trash')
        self.assertEquals(response.status_code, 403)

    def test_user_page_view_lite_cannot_access_trash(self):
        Generators.premium_subscription(self.user, "AstroBin Lite")
        self.client.login(username="user", password="password")
        response = self.client.get(reverse('user_page', args=('user',)) + '?trash')
        self.assertEquals(response.status_code, 403)

    def test_user_page_view_lite_autorenew_cannot_access_trash(self):
        Generators.premium_subscription(self.user, "AstroBin Lite (autorenew)")
        self.client.login(username="user", password="password")
        response = self.client.get(reverse('user_page', args=('user',)) + '?trash')
        self.assertEquals(response.status_code, 403)

    def test_user_page_view_lite_2020_cannot_access_trash(self):
        Generators.premium_subscription(self.user, "AstroBin Lite 2020+")
        self.client.login(username="user", password="password")
        response = self.client.get(reverse('user_page', args=('user',)) + '?trash')
        self.assertEquals(response.status_code, 403)

    def test_user_page_view_premium_cannot_access_trash(self):
        Generators.premium_subscription(self.user, "AstroBin Premium")
        self.client.login(username="user", password="password")
        response = self.client.get(reverse('user_page', args=('user',)) + '?trash')
        self.assertEquals(response.status_code, 403)

    def test_user_page_view_premium_autorenew_cannot_access_trash(self):
        Generators.premium_subscription(self.user, "AstroBin Premium (autorenew)")
        self.client.login(username="user", password="password")
        response = self.client.get(reverse('user_page', args=('user',)) + '?trash')
        self.assertEquals(response.status_code, 403)

    def test_user_page_view_premium_2020_cannot_access_trash(self):
        Generators.premium_subscription(self.user, "AstroBin Premium 2020+")
        self.client.login(username="user", password="password")
        response = self.client.get(reverse('user_page', args=('user',)) + '?trash')
        self.assertEquals(response.status_code, 403)

    def test_user_page_view_ultimate_2020_can_access_trash(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.client.login(username="user", password="password")
        response = self.client.get(reverse('user_page', args=('user',)) + '?trash')
        self.assertEquals(response.status_code, 200)

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_user_page_view(self, retrieve_primary_thumbnails):
        today = date.today()

        # Test simple access
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "TEST BASIC IMAGE")
        response = self.client.get(reverse('user_page', args=('user',)))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)
        image.delete()

        # Test staging when anonymous
        self.client.logout()
        response = self.client.get(
            reverse('user_page', args=('user',)) + '?staging')
        self.assertEquals(response.status_code, 403)
        self.client.login(username="user", password="password")

        # Test staging images
        image = self._do_upload('astrobin/fixtures/test.jpg', "TEST STAGING IMAGE", True)
        response = self.client.get(
            reverse('user_page', args=('user',)) + '?staging')

        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        response = self.client.get(reverse('user_page', args=('user',)))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, False)

        image.delete()

        # Test "upload time" sorting
        image1 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE1")
        image2 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE2")
        image1.uploaded = today
        image1.save(keep_deleted=True)
        image2.uploaded = today + timedelta(1)
        image2.save(keep_deleted=True)

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=uploaded")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.content.find("IMAGE2") < response.content.find("IMAGE1"), True)

        image1.delete()
        image2.delete()

        # Test "acquisition time" sorting
        image1 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE1")
        image2 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE2")
        acquisition1 = Acquisition.objects.create(image=image1, date=today)
        acquisition2 = Acquisition.objects.create(
            image=image2, date=today + timedelta(1))
        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=acquired")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.content.find("IMAGE2") < response.content.find("IMAGE1"), True)

        acquisition1.delete()
        acquisition2.delete()
        image1.delete()
        image2.delete()

        # Test "subject type" sub-section
        image1 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE1_DEEP")
        image2 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE2_SOLAR")
        image3 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE3_WIDE")
        image4 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE4_TRAILS")
        image5 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE5_GEAR")
        image6 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE6_OTHER")

        image1.subject_type = SubjectType.DEEP_SKY
        image1.save(keep_deleted=True)
        image2.subject_type = SubjectType.SOLAR_SYSTEM
        image2.save(keep_deleted=True)
        image3.subject_type = SubjectType.WIDE_FIELD
        image3.save(keep_deleted=True)
        image4.subject_type = SubjectType.STAR_TRAILS
        image4.save(keep_deleted=True)
        image5.subject_type = SubjectType.GEAR
        image5.save(keep_deleted=True)
        image6.subject_type = SubjectType.OTHER
        image6.save(keep_deleted=True)

        response = self.client.get(reverse('user_page', args=('user',)) + "?sub=subject")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args=('user',)) + "?sub=subject&active=DEEP")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args=('user',)) + "?sub=subject&active=SOLAR")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, True)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args=('user',)) + "?sub=subject&active=WIDE")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, True)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args=('user',)) + "?sub=subject&active=TRAILS")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, True)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args=('user',)) + "?sub=subject&active=GEAR")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, True)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args=('user',)) + "?sub=subject&active=OTHER")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, True)

        image1.delete()
        image2.delete()
        image3.delete()
        image4.delete()
        image5.delete()
        image6.delete()

        # Test "year" sub-section
        image1 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE1")
        image2 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE2")
        image3 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE3")

        acquisition1 = Acquisition.objects.create(image=image1, date=today)
        acquisition2 = Acquisition.objects.create(
            image=image2, date=today - timedelta(365))

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=year")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=year&active=%d" % today.year)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=year&active=%d" % (today.year - 1))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, True)
        self.assertEquals(image3.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=year&active=0")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, True)

        acquisition1.delete()
        acquisition2.delete()
        image1.delete()
        image2.delete()
        image3.delete()

        # Test "gear" sub-section
        image1 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE1")
        image2 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE2")
        image3 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE3")
        image4 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE4")

        image3.subject_type = SubjectType.SOLAR_SYSTEM
        image3.save(keep_deleted=True)
        image4.subject_type = SubjectType.GEAR
        image4.save(keep_deleted=True)

        telescope1 = Telescope.objects.create(name="TELESCOPE1")
        telescope2 = Telescope.objects.create(name="TELESCOPE2")
        image1.imaging_telescopes.add(telescope1)
        image1.save(keep_deleted=True)
        image2.imaging_telescopes.add(telescope2)
        image2.save(keep_deleted=True)

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=gear&active=%d" % telescope1.pk)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=gear&active=%d" % telescope2.pk)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, True)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=gear&active=0")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, True)
        self.assertEquals(image4.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=gear&active=-1")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, True)

        telescope1.delete()
        telescope2.delete()
        image1.delete()
        image2.delete()
        image3.delete()
        image4.delete()

        # Test "no data" sub-section
        image = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE_NODATA")
        image.subject_type = SubjectType.DEEP_SKY
        image.save(keep_deleted=True)
        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=nodata")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        image.subject_type = SubjectType.SOLAR_SYSTEM
        image.solar_system_main_subject = None
        image.save(keep_deleted=True)
        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=nodata")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=nodata&active=GEAR")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        response = self.client.get(
            reverse('user_page', args=('user',)) + "?sub=nodata&active=ACQ")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        # Users with at least one spam image should be 404
        image.moderator_decision = 2
        image.save(keep_deleted=True)
        response = self.client.get(reverse('user_page', args=('user',)))
        self.assertEquals(response.status_code, 404)

        image.delete()
        self.client.logout()

    def test_user_page_commercial_products_view(self):
        url = reverse(
            'user_page_commercial_products', args=(self.user.username,))

        # Test anonymous
        response = self.client.get(url)
        self.assertEquals(response.status_code, 403)

        # Test non producer / non retailer
        self.client.login(username="user", password="password")
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['user_is_producer'], False)
        self.assertEquals(response.context['user_is_retailer'], False)
        self.assertEquals(len(response.context['commercial_gear_list']), 0)
        self.assertEquals(len(response.context['retailed_gear_list']), 0)

        # Test producer
        self.user.groups.add(self.producers)
        commercial_telescope = CommercialGear.objects.create(
            producer=self.user)
        telescope = Telescope.objects.create(
            name="Test producer telescope", commercial=commercial_telescope)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['user_is_producer'], True)
        self.assertEquals(response.context['user_is_retailer'], False)
        self.assertEquals(len(response.context['commercial_gear_list']), 1)
        self.assertEquals(len(response.context['retailed_gear_list']), 0)
        self.assertEquals('claim_commercial_gear_form' in response.context, True)
        self.assertEquals('merge_commercial_gear_form' in response.context, True)
        self.user.groups.remove(self.producers)
        commercial_telescope.delete()
        telescope.delete()

        # TODO: test retailers

        self.client.logout()

    @override_settings(PREMIUM_RESTRICTS_IOTD=False)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_user_profile_exclude_from_competitions(self, retrieve_primary_thumbnails):
        self.client.login(username="user", password="password")
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = Image.objects_including_wip.all()[0]

        submitter = User.objects.create_user('submitter', 'submitter_1@test.com', 'password')
        submitters = Group.objects.create(name='iotd_submitters')
        submitters.user_set.add(submitter)
        reviewer = User.objects.create_user('reviewer', 'reviewer_1@test.com', 'password')
        reviewers = Group.objects.create(name='iotd_reviewers')
        reviewers.user_set.add(reviewer)
        judge = User.objects.create_user('judge', 'judge_1@test.com', 'password')
        judges = Group.objects.create(name='iotd_judges')
        judges.user_set.add(judge)
        submission = IotdSubmission.objects.create(submitter=submitter, image=image)
        vote = IotdVote.objects.create(reviewer=reviewer, image=image)
        iotd = Iotd.objects.create(judge=judge, image=image, date=datetime.now().date())

        profile = self.user.userprofile
        profile.exclude_from_competitions = True
        profile.save(keep_deleted=True)
        image = Image.objects_including_wip.get(pk=image.pk)

        # Check that the IOTD banner is not visible
        response = self.client.get(reverse('image_detail', args=(image.get_id(),)))
        self.assertNotContains(response, "iotd-ribbon")

        # Check that the IOTD badge is not visible
        response = self.client.get(reverse('user_page', args=(self.user.username,)))
        self.assertNotContains(response, 'iotd-badge')

        # Check that the Top Pick badge is not visible
        iotd.delete()
        response = self.client.get(reverse('user_page', args=(self.user.username,)))
        self.assertNotContains(response, 'top-pick-badge')

        # Check that the top100 badge is not visible
        self.assertNotContains(response, 'top100-badge')

        submitter.delete()
        reviewer.delete()
        judge.delete()

        submitters.delete()
        reviewers.delete()
        judges.delete()

        submission.delete()
        vote.delete()

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_corrupted_images_not_shown_to_others(self, retrieve_primary_thumbnails):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "TEST IMAGE")
        image.corrupted = True
        image.save()
        self.client.logout()

        response = self.client.get(reverse("user_page", args=(self.user.username,)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "data-id=\"%d\"" % image.pk)

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_corrupted_images_shown_to_owner(self, retrieve_primary_thumbnails):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "TEST IMAGE")
        image.corrupted = True
        image.save()

        response = self.client.get(reverse("user_page", args=(self.user.username,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-id=\"%d\"" % image.pk)

    def test_bookmarks(self):
        self.client.login(username="user", password="password")
        response = self.client.get(reverse("user_page_bookmarks", args=(self.user.username,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_liked(self, retrieve_primary_thumbnails):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "TEST IMAGE")
        self.client.logout()

        prop = ToggleProperty.objects.create_toggleproperty('like', image, self.user_2)
        response = self.client.get(reverse("user_page_liked", args=(self.user_2.username,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-id=\"%d\"" % image.pk)

    def test_plots(self):
        self.client.login(username="user", password="password")
        response = self.client.get(reverse("user_page_plots", args=(self.user.username,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_profile_updated_when_saved(self):
        updated = self.user.userprofile.updated
        self.user.first_name = "foo"
        self.user.save()

        profile = UserProfile.objects.get(user=self.user)
        self.assertNotEquals(updated, profile.updated)

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_profile_updated_when_image_saved(self, retrieve_primary_thumbnails):
        updated = self.user.userprofile.updated

        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "TEST IMAGE")

        profile = UserProfile.objects.get(user=self.user)
        self.assertNotEquals(updated, profile.updated)

        updated = self.user.userprofile.updated
        image.title = "TEST IMAGE UPDATED"
        image.save(keep_deleted=True)

        profile = UserProfile.objects.get(user=self.user)
        self.assertNotEquals(updated, profile.updated)

        image.delete()
        self.client.logout()

    def test_profile_softdelete(self):
        user = User.objects.create_user(
            username="softdelete", email="softdelete@example.com",
            password="password")

        # Deleting the User really deletes stuff
        user.delete()
        self.assertFalse(User.objects.filter(username="softdelete").exists())
        self.assertFalse(UserProfile.objects.filter(user__username="softdelete").exists())
        self.assertFalse(UserProfile.all_objects.filter(user__username="softdelete").exists())

        user = User.objects.create_user(
            username="softdelete", email="softdelete@example.com",
            password="password")
        profile = UserProfile.objects.get(user=user)

        # Deleting the profile only soft-deletes
        profile.delete()
        self.assertTrue(User.objects.filter(username="softdelete").exists())
        self.assertEqual(False, User.objects.get(username="softdelete").is_active)
        self.assertFalse(UserProfile.objects.filter(user__username="softdelete").exists())
        self.assertTrue(UserProfile.all_objects.filter(user__username="softdelete").exists())

    def test_bounced_email_alert(self):
        bounce = Bounce.objects.create(
            hard=True,
            bounce_type="Permanent",
            address="user@example.com",
            mail_timestamp=timezone.now())

        self.client.login(username="user", password="password")
        response = self.client.get(reverse('index'))
        self.assertContains(response, "Change your e-mail")

        bounce.delete()

    def test_corrupted_image_not_shown_to_anon(self):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "CORRUPTED_IMAGE")
        image.corrupted = True
        image.save()
        self.client.logout()

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertEquals(200, response.status_code)
        self.assertNotContains(response, "CORRUPTED_IMAGE")

        image.delete()

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_corrupted_final_image_revision_not_shown_to_anon(self):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "CORRUPTED_IMAGE")
        revision = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision.corrupted = True
        revision.save()
        self.client.logout()

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertEquals(200, response.status_code)
        self.assertNotContains(response, "CORRUPTED_IMAGE")

        image.delete()
        revision.delete()

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_corrupted_image_with_ok_final_revision_shown_to_anon(self):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "CORRUPTED_IMAGE")
        image.corrupted = True
        image.save()
        revision = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        self.client.logout()

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertEquals(200, response.status_code)
        self.assertContains(response, "CORRUPTED_IMAGE")

        image.delete()
        revision.delete()

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_corrupted_image_with_ok_non_final_revision_not_shown_to_anon(self):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "CORRUPTED_IMAGE")
        revision = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision.is_final = False
        revision.save()

        image.corrupted = True
        image.is_final = True
        image.save()

        self.client.logout()

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertEquals(200, response.status_code)
        self.assertNotContains(response, "CORRUPTED_IMAGE")

        image.delete()
        revision.delete()

    def test_corrupted_image_shown_to_owner(self):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "CORRUPTED_IMAGE")
        image.corrupted = True
        image.save()

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertEquals(200, response.status_code)
        self.assertContains(response, "CORRUPTED_IMAGE")

        response = self.client.get(reverse('user_page', args=('user',)) + "?corrupted")

        self.assertEquals(200, response.status_code)
        self.assertContains(response, "CORRUPTED_IMAGE")

        image.delete()

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_corrupted_final_image_revision_shown_to_owner(self):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "CORRUPTED_IMAGE")
        revision = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision.corrupted = True
        revision.save()

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertEquals(200, response.status_code)
        self.assertContains(response, "CORRUPTED_IMAGE")

        response = self.client.get(reverse('user_page', args=('user',)) + "?corrupted")

        self.assertEquals(200, response.status_code)
        self.assertContains(response, "CORRUPTED_IMAGE")

        image.delete()
        revision.delete()

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_corrupted_image_with_ok_final_revision_shown_to_owner(self):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "CORRUPTED_IMAGE")
        image.corrupted = True
        image.save()
        revision = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertEquals(200, response.status_code)
        self.assertContains(response, "CORRUPTED_IMAGE")

        response = self.client.get(reverse('user_page', args=('user',)) + "?corrupted")

        self.assertEquals(200, response.status_code)
        self.assertNotContains(response, "CORRUPTED_IMAGE")

        image.delete()
        revision.delete()

    @override_settings(PREMIUM_MAX_REVISIONS_FREE_2020=sys.maxsize)
    def test_corrupted_image_with_ok_non_final_revision_shown_to_owner(self):
        self.client.login(username="user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "CORRUPTED_IMAGE")
        revision = self._do_upload_revision(image, 'astrobin/fixtures/test.jpg')
        revision.is_final = False
        revision.save()

        image.corrupted = True
        image.is_final = True
        image.save()

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertEquals(200, response.status_code)
        self.assertContains(response, "CORRUPTED_IMAGE")

        response = self.client.get(reverse('user_page', args=('user',)) + "?corrupted")

        self.assertEquals(200, response.status_code)
        self.assertContains(response, "CORRUPTED_IMAGE")

        image.delete()
        revision.delete()

    @override_settings(PREMIUM_MAX_IMAGES_FREE_2020=123)
    def test_user_page_subscription_free(self):
        image = Generators.image()
        image.user = self.user
        image.save()

        self.client.login(username='user', password='password')

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertContains(response, "<h4>Subscription</h4>", html=True)
        self.assertContains(response, "<strong data-test='subscription-type'>AstroBin Free</strong>", html=True)
        self.assertNotContains(response, "data-test=\"expiration-date\"")
        self.assertContains(response, "<strong data-test='images-used'>0 / 123</strong>", html=True)

        self.client.logout()
        image.delete()

    @override_settings(PREMIUM_MAX_IMAGES_LITE=123)
    def test_user_page_subscription_lite(self):
        image = Generators.image()
        image.user = self.user
        image.save()

        us = Generators.premium_subscription(self.user, "AstroBin Lite")

        self.client.login(username='user', password='password')

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertContains(response, "<h4>Subscription</h4>", html=True)
        self.assertContains(response, "<strong data-test='subscription-type'>AstroBin Lite</strong>", html=True)
        self.assertContains(
            response,
            "<strong data-test='expiration-date'>" +
            formats.date_format(us.expires, "SHORT_DATE_FORMAT") +
            "</strong>",
            html=True)
        self.assertContains(response, "<strong data-test='images-used'>0 / 123</strong>", html=True)

        self.client.logout()
        us.delete()
        image.delete()

    @override_settings(PREMIUM_MAX_IMAGES_LITE_2020=123)
    def test_user_page_subscription_lite_2020(self):
        image = Generators.image()
        image.user = self.user
        image.save()

        us = Generators.premium_subscription(self.user, "AstroBin Lite 2020+")

        self.client.login(username='user', password='password')

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertContains(response, "<h4>Subscription</h4>", html=True)
        self.assertContains(response, "<strong data-test='subscription-type'>AstroBin Lite</strong>", html=True)
        self.assertContains(
            response,
            "<strong data-test='expiration-date'>" +
            formats.date_format(us.expires, "SHORT_DATE_FORMAT") +
            "</strong>",
            html=True)
        self.assertContains(response, "<strong data-test='images-used'>0 / 123</strong>", html=True)

        self.client.logout()
        us.delete()
        image.delete()

    def test_user_page_subscription_premium(self):
        image = Generators.image()
        image.user = self.user
        image.save()

        us = Generators.premium_subscription(self.user, "AstroBin Premium")

        self.client.login(username='user', password='password')

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertContains(response, "<h4>Subscription</h4>", html=True)
        self.assertContains(response, "<strong data-test='subscription-type'>AstroBin Premium</strong>", html=True)
        self.assertContains(
            response,
            "<strong data-test='expiration-date'>" +
            formats.date_format(us.expires, "SHORT_DATE_FORMAT") +
            "</strong>",
            html=True)
        self.assertContains(response, "<strong data-test='images-used'>0 / &infin;</strong>", html=True)

        self.client.logout()
        us.delete()
        image.delete()

    @override_settings(PREMIUM_MAX_IMAGES_PREMIUM_2020=123)
    def test_user_page_subscription_premium_2020(self):
        image = Generators.image()
        image.user = self.user
        image.save()

        us = Generators.premium_subscription(self.user, "AstroBin Premium 2020+")

        self.client.login(username='user', password='password')

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertContains(response, "<h4>Subscription</h4>", html=True)
        self.assertContains(response, "<strong data-test='subscription-type'>AstroBin Premium</strong>", html=True)
        self.assertContains(
            response,
            "<strong data-test='expiration-date'>" +
            formats.date_format(us.expires, "SHORT_DATE_FORMAT") +
            "</strong>",
            html=True)
        self.assertContains(response, "<strong data-test='images-used'>0 / &infin;</strong>", html=True)

        self.client.logout()
        us.delete()
        image.delete()

    def test_user_page_subscription_ultimate(self):
        image = Generators.image()
        image.user = self.user
        image.save()

        us = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")

        self.client.login(username='user', password='password')

        response = self.client.get(reverse('user_page', args=('user',)))

        self.assertContains(response, "<h4>Subscription</h4>", html=True)
        self.assertContains(response, "<strong data-test='subscription-type'>AstroBin Ultimate</strong>", html=True)
        self.assertContains(
            response,
            "<strong data-test='expiration-date'>" +
            formats.date_format(us.expires, "SHORT_DATE_FORMAT") +
            "</strong>",
            html=True)
        self.assertContains(response, "<strong data-test='images-used'>0 / &infin;</strong>", html=True)

        self.client.logout()
        us.delete()
        image.delete()

    @override_settings(ADS_ENABLED=True)
    def test_user_preferences_allow_astronomy_ads_free(self):
        self.client.login(username='user', password='password')
        self.assertContains(
            self.client.get(reverse('profile_edit_preferences')),
            'name="allow_astronomy_ads" disabled')
        self.client.logout()

    @override_settings(ADS_ENABLED=True)
    def test_user_preferences_allow_astronomy_ads_lite(self):
        self.client.login(username='user', password='password')
        us = Generators.premium_subscription(self.user, "AstroBin Lite")
        self.assertNotContains(
            self.client.get(reverse('profile_edit_preferences')),
            'name="allow_astronomy_ads" disabled')
        self.client.logout()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    def test_user_preferences_allow_astronomy_ads_lite_2020(self):
        self.client.login(username='user', password='password')
        us = Generators.premium_subscription(self.user, "AstroBin Lite 2020+")
        self.assertContains(
            self.client.get(reverse('profile_edit_preferences')),
            'name="allow_astronomy_ads" disabled')
        self.client.logout()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    def test_user_preferences_allow_astronomy_ads_premium(self):
        self.client.login(username='user', password='password')
        us = Generators.premium_subscription(self.user, "AstroBin Premium")
        self.assertNotContains(
            self.client.get(reverse('profile_edit_preferences')),
            'name="allow_astronomy_ads" disabled')
        self.client.logout()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    def test_user_preferences_allow_astronomy_ads_premium_2020(self):
        self.client.login(username='user', password='password')
        us = Generators.premium_subscription(self.user, "AstroBin Premium 2020+")
        self.assertNotContains(
            self.client.get(reverse('profile_edit_preferences')),
            'name="allow_astronomy_ads" disabled')
        self.client.logout()
        us.delete()

    @override_settings(ADS_ENABLED=True)
    def test_user_preferences_allow_astronomy_ads_ultimate_2020(self):
        self.client.login(username='user', password='password')
        us = Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.assertNotContains(
            self.client.get(reverse('profile_edit_preferences')),
            'name="allow_astronomy_ads" disabled')
        self.client.logout()
        us.delete()

    def test_user_can_access_trash_free(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('user_page', args=('user',)) + "?trash")
        self.assertEquals(403, response.status_code)

    def test_user_can_access_trash_lite(self):
        self.client.login(username='user', password='password')
        Generators.premium_subscription(self.user, "AstroBin Lite")
        response = self.client.get(reverse('user_page', args=('user',)) + "?trash")
        self.assertEquals(403, response.status_code)

    def test_user_can_access_trash_lite_autorenew(self):
        self.client.login(username='user', password='password')
        Generators.premium_subscription(self.user, "AstroBin Lite (autorenew)")
        response = self.client.get(reverse('user_page', args=('user',)) + "?trash")
        self.assertEquals(403, response.status_code)

    def test_user_can_access_trash_lite_2020(self):
        self.client.login(username='user', password='password')
        Generators.premium_subscription(self.user, "AstroBin Lite 2020+")
        response = self.client.get(reverse('user_page', args=('user',)) + "?trash")
        self.assertEquals(403, response.status_code)

    def test_user_can_access_trash_premium(self):
        self.client.login(username='user', password='password')
        Generators.premium_subscription(self.user, "AstroBin Premium")
        response = self.client.get(reverse('user_page', args=('user',)) + "?trash")
        self.assertEquals(403, response.status_code)

    def test_user_can_access_trash_premium_autorenew(self):
        self.client.login(username='user', password='password')
        Generators.premium_subscription(self.user, "AstroBin Premium (autorenew)")
        response = self.client.get(reverse('user_page', args=('user',)) + "?trash")
        self.assertEquals(403, response.status_code)

    def test_user_can_access_trash_premium_2020(self):
        self.client.login(username='user', password='password')
        Generators.premium_subscription(self.user, "AstroBin Premium 2020+")
        response = self.client.get(reverse('user_page', args=('user',)) + "?trash")
        self.assertEquals(403, response.status_code)

    def test_user_can_access_trash_ultimate_2020(self):
        self.client.login(username='user', password='password')
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        response = self.client.get(reverse('user_page', args=('user',)) + "?trash")
        self.assertEquals(200, response.status_code)

    def test_user_can_access_data_download_free(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('profile_download_data'))
        self.assertRedirects(response, '/accounts/login/?next=' + reverse('profile_download_data'))

    def test_user_can_access_data_download_lite(self):
        Generators.premium_subscription(self.user, "AstroBin Lite")
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('profile_download_data'))
        self.assertRedirects(response, '/accounts/login/?next=' + reverse('profile_download_data'))

    def test_user_can_access_data_download_lite_autorenew(self):
        Generators.premium_subscription(self.user, "AstroBin Lite (autorenew)")
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('profile_download_data'))
        self.assertRedirects(response, '/accounts/login/?next=' + reverse('profile_download_data'))

    def test_user_can_access_data_download_lite_2020(self):
        Generators.premium_subscription(self.user, "AstroBin Lite 2020+")
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('profile_download_data'))
        self.assertRedirects(response, '/accounts/login/?next=' + reverse('profile_download_data'))

    def test_user_can_access_data_download_premium(self):
        Generators.premium_subscription(self.user, "AstroBin Premium")
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('profile_download_data'))
        self.assertEquals(response.status_code, 200)

    def test_user_can_access_data_download_premium_autorenew(self):
        Generators.premium_subscription(self.user, "AstroBin Premium (autorenew)")
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('profile_download_data'))
        self.assertEquals(response.status_code, 200)

    def test_user_can_access_data_download_premium_2020(self):
        Generators.premium_subscription(self.user, "AstroBin Premium 2020+")
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('profile_download_data'))
        self.assertEquals(response.status_code, 200)

    def test_user_can_access_data_download_ultimate_2020(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('profile_download_data'))
        self.assertEquals(response.status_code, 200)

    def test_download_data_view_quota(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.client.login(username='user', password='password')

        response = self.client.get(reverse('profile_download_data'))
        self.assertFalse(response.context["exceeded_requests_quota"])

        DataDownloadRequest.objects.create(user=self.user)

        response = self.client.get(reverse('profile_download_data'))
        self.assertTrue(response.context["exceeded_requests_quota"])
