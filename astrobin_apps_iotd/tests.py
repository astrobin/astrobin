# Django
from datetime import datetime, timedelta

# Django
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.test import TestCase

# AstroBin
from astrobin.models import Image

# This app
from astrobin_apps_iotd.models import IotdSubmission


class IotdTest(TestCase):
    def setUp(self):
        self.submitters = Group.objects.create(name = 'iotd_submitters')

        self.user = User.objects.create_user(
            'user', 'user@test.com', 'password')
        self.submitter = User.objects.create_user(
            'submitter', 'submitter@test.com', 'password')
        self.submitters.user_set.add(self.submitter)

        self.image = Image.objects.create(user = self.user)

    def tearDown(self):
        self.submitters.delete()
        self.submitter.delete()
        self.user.delete()
        self.image.delete()

    def test_submission_model(self):
        self.image.user = self.user
        self.image.uploaded =\
            datetime.now() -\
            timedelta(
                weeks = settings.IOTD_SUBMISSION_WINDOW_WEEKS,
                days = 1)
        self.image.save()

        # User must be submitter
        with self.assertRaises(ValidationError):
            IotdSubmission.objects.create(
                submitter = self.user,
                image = self.image)

        # Image must be recent enough
        self.image.user = self.submitter
        self.image.save()
        with self.assertRaises(ValidationError):
            IotdSubmission.objects.create(
                submitter = self.submitter,
                image = self.image)

        # Image must not be WIP
        self.image.uploaded = datetime.now()
        self.image.is_wip = True
        self.image.save()
        with self.assertRaises(ValidationError):
            IotdSubmission.objects.create(
                submitter = self.submitter,
                image = self.image)

        # All OK
        self.image.is_wip = False
        self.image.save()
        submission = IotdSubmission.objects.create(
            submitter = self.submitter,
            image = self.image)
        self.assertEqual(submission.submitter, self.submitter)
        self.assertEqual(submission.image, self.image)

        # Image cannot be submitted again
        with self.assertRaises(ValidationError):
            IotdSubmission.objects.create(
                submitter = self.submitter,
                image = self.image)

        # Test max daily
        with self.assertRaises(ValidationError):
            image2 = Image.objects.create(user = self.submitter)
            with self.settings(IOTD_SUBMISSION_MAX_PER_DAY = 1):
                IotdSubmission.objects.create(
                    submitter = self.submitter,
                    image = image2)

    def test_submission_create_view(self):
        url = reverse_lazy('iotd_submission_create')

        # Login required
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # Only submitters allowed
        self.client.login(username = 'user', password = 'password')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # GET not allowed
        self.client.login(username = 'submitter', password = 'password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Success
        response = self.client.post(url, {
            'submitter': self.submitter.pk,
            'image': self.image.pk,
        })
        self.assertEqual(IotdSubmission.objects.count(), 1)
