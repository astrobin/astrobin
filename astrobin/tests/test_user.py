# Python
from datetime import date

# Django
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.utils import timezone

# Third party
from django_bouncy.models import Bounce
from mock import patch
from toggleproperties.models import ToggleProperty

# AstroBin
from astrobin.models import (
    Acquisition,
    CommercialGear,
    Telescope,
    UserProfile
)
from astrobin_apps_iotd.models import *


class UserTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username = "user", email = "user@example.com",
            password = "password")
        self.user_2 = User.objects.create_user(
            username = "user_2", email = "user_2@example.com",
            password = "password")

        self.producers = Group.objects.create(name = 'Producers')
        self.retailers = Group.objects.create(name = 'Retailers')
        self.payers = Group.objects.create(name = 'Paying')

    def tearDown(self):
        self.user.delete()
        self.user_2.delete()
        self.producers.delete()
        self.retailers.delete()
        self.payers.delete()

    def _get_last_image(self):
        return Image.objects_including_wip.all().order_by('-id')[0]

    def _do_upload(self, filename, title = "TEST IMAGE", wip = False):
        data = {'image_file': open(filename, 'rb')}
        if wip:
            data['wip'] = True

        patch('astrobin.tasks.retrieve_primary_thumbnails.delay')
        self.client.post(
            reverse('image_upload_process'),
            data,
            follow = True)

        image = self._get_last_image()
        if title:
            image.title = title
            image.save()

        return image

    def test_user_page_view(self):
        today = date.today()

        # Test simple access
        self.client.login(username = "user", password="password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "TEST BASIC IMAGE")
        response = self.client.get(reverse('user_page', args = ('user',)))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)
        image.delete()

        # Test staging when anonymous
        self.client.logout()
        response = self.client.get(
            reverse('user_page', args = ('user',)) + '?staging')
        self.assertEquals(response.status_code, 403)
        self.client.login(username = "user", password="password")

        # Test staging images
        image = self._do_upload('astrobin/fixtures/test.jpg', "TEST STAGING IMAGE", True)
        response = self.client.get(
            reverse('user_page', args = ('user',)) + '?staging')

        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        response = self.client.get(reverse('user_page', args = ('user',)))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, False)

        image.delete()

        # Test "upload time" sorting
        image1 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE1")
        image2 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE2")
        image1.uploaded = today; image1.save()
        image2.uploaded = today + timedelta(1); image2.save()

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=uploaded")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.content.find("IMAGE2") < response.content.find("IMAGE1"), True)

        image1.delete()
        image2.delete()

        # Test "acquisition time" sorting
        image1 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE1")
        image2 = self._do_upload('astrobin/fixtures/test.jpg', "IMAGE2")
        acquisition1 = Acquisition.objects.create(image = image1, date = today)
        acquisition2 = Acquisition.objects.create(
            image = image2, date = today + timedelta(1))
        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=acquired")
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

        image1.subject_type = 100; image1.save()
        image2.subject_type = 200; image2.save()
        image3.subject_type = 300; image3.save()
        image4.subject_type = 400; image4.save()
        image5.subject_type = 500; image5.save()
        image6.subject_type = 600; image6.save()

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=DEEP")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=SOLAR")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, True)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=WIDE")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, True)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=TRAILS")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, True)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=GEAR")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, True)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=OTHER")
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

        acquisition1 = Acquisition.objects.create(image = image1, date = today)
        acquisition2 = Acquisition.objects.create(
            image = image2, date = today - timedelta(365))

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=year")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=year&active=%d" % today.year)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=year&active=%d" % (today.year - 1))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, True)
        self.assertEquals(image3.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=year&active=0")
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

        image3.subject_type = 200; image3.save()
        image4.subject_type = 500; image4.save()


        telescope1 = Telescope.objects.create(name = "TELESCOPE1")
        telescope2 = Telescope.objects.create(name = "TELESCOPE2")
        image1.imaging_telescopes.add(telescope1)
        image1.save()
        image2.imaging_telescopes.add(telescope2)
        image2.save()

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=gear&active=%d" % telescope1.pk)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=gear&active=%d" % telescope2.pk)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, True)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=gear&active=0")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, True)
        self.assertEquals(image4.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=gear&active=-1")
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
        image.subject_type = 100
        image.save()
        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=nodata")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        image.subject_type = 200
        image.solar_system_main_subject = None
        image.save()
        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=nodata")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=nodata&active=GEAR")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=nodata&active=ACQ")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        # Users with at least one spam image should be 404
        image.moderator_decision = 2
        image.save()
        response = self.client.get(reverse('user_page', args = ('user',)))
        self.assertEquals(response.status_code, 404)

        image.delete()
        self.client.logout()

    def test_user_page_commercial_products_view(self):
        url = reverse(
            'user_page_commercial_products', args = (self.user.username,))

        # Test anonymous
        response = self.client.get(url)
        self.assertEquals(response.status_code, 403)

        # Test non producer / non retailer
        self.client.login(username = "user", password = "password")
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['user_is_producer'], False)
        self.assertEquals(response.context['user_is_retailer'], False)
        self.assertEquals(len(response.context['commercial_gear_list']), 0)
        self.assertEquals(len(response.context['retailed_gear_list']), 0)

        # Test producer
        self.user.groups.add(self.producers)
        commercial_telescope = CommercialGear.objects.create(
            producer = self.user)
        telescope = Telescope.objects.create(
            name = "Test producer telescope", commercial = commercial_telescope)
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

    def test_user_profile_exclude_from_competitions(self):
        self.client.login(username = "user", password="password")
        self._do_upload('astrobin/fixtures/test.jpg')
        self.client.logout()

        image = Image.objects_including_wip.all()[0]

        submitter = User.objects.create_user('submitter', 'submitter_1@test.com', 'password')
        submitters = Group.objects.create(name = 'iotd_submitters')
        submitters.user_set.add(submitter)
        reviewer = User.objects.create_user('reviewer', 'reviewer_1@test.com', 'password')
        reviewers = Group.objects.create(name = 'iotd_reviewers')
        reviewers.user_set.add(reviewer)
        judge = User.objects.create_user('judge', 'judge_1@test.com', 'password')
        judges = Group.objects.create(name = 'iotd_judges')
        judges.user_set.add(judge)
        submission = IotdSubmission.objects.create(submitter = submitter, image = image)
        vote = IotdVote.objects.create(reviewer = reviewer, image = image)
        iotd = Iotd.objects.create(judge = judge, image = image, date = datetime.now().date())

        profile = self.user.userprofile
        profile.exclude_from_competitions = True
        profile.save()
        image = Image.objects_including_wip.get(pk = image.pk)

        # Check that the IOTD banner is not visible
        response = self.client.get(reverse('image_detail', args = (image.pk,)))
        self.assertNotContains(response, "iotd-ribbon")

        # Check that the IOTD badge is not visible
        response = self.client.get(reverse('user_page', args = (self.user.username,)))
        self.assertNotContains(response, 'iotd-badge')

        # Check that the Top Pick badge is not visible
        iotd.delete()
        response = self.client.get(reverse('user_page', args = (self.user.username,)))
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

    def test_bookmarks(self):
        self.client.login(username = "user", password = "password")
        response = self.client.get(reverse("user_page_bookmarks", args = (self.user.username,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_liked(self):
        self.client.login(username = "user", password = "password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "TEST IMAGE")
        self.client.logout()

        prop = ToggleProperty.objects.create_toggleproperty('like', image, self.user_2)
        response = self.client.get(reverse("user_page_liked", args = (self.user_2.username,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-id=\"%d\"" % image.pk)

    def test_plots(self):
        self.client.login(username = "user", password = "password")
        response = self.client.get(reverse("user_page_plots", args = (self.user.username,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_profile_updated_when_saved(self):
        updated = self.user.userprofile.updated
        self.user.first_name = "foo"
        self.user.save()

        profile = UserProfile.objects.get(user = self.user)
        self.assertNotEquals(updated, profile.updated)

    def test_profile_updated_when_image_saved(self):
        updated = self.user.userprofile.updated

        self.client.login(username = "user", password = "password")
        image = self._do_upload('astrobin/fixtures/test.jpg', "TEST IMAGE")

        profile = UserProfile.objects.get(user = self.user)
        self.assertNotEquals(updated, profile.updated)

        updated = self.user.userprofile.updated
        image.title = "TEST IMAGE UPDATED"
        image.save()

        profile = UserProfile.objects.get(user = self.user)
        self.assertNotEquals(updated, profile.updated)

        image.delete()
        self.client.logout()

    def test_profile_softdelete(self):
        user = User.objects.create_user(
            username = "softdelete", email = "softdelete@example.com",
            password = "password")

        # Deleting the User really deletes stuff
        user.delete()
        self.assertFalse(User.objects.filter(username="softdelete").exists())
        self.assertFalse(UserProfile.objects.filter(user__username="softdelete").exists())
        self.assertFalse(UserProfile.all_objects.filter(user__username="softdelete").exists())

        user = User.objects.create_user(
            username = "softdelete", email = "softdelete@example.com",
            password = "password")
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

        self.client.login(username = "user", password="password")
        response = self.client.get(reverse('index'))
        self.assertContains(response, "Change your e-mail")

        bounce.delete()
