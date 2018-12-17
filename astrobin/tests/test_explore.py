# Django
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse_lazy
from django.test import TestCase

# Other apps
from mock import patch

from astrobin_apps_iotd.models import IotdSubmission, IotdVote

# AstroBin
from astrobin.models import Image


class ExploreTest(TestCase):
    def setUp(self):
        patch('astrobin.tasks.retrieve_primary_thumbnails.delay')

        self.submitter = User.objects.create_user('submitter_1', 'submitter_1@test.com', 'password')
        self.submitters = Group.objects.create(name='iotd_submitters')
        self.submitters.user_set.add(self.submitter)

        self.reviewer = User.objects.create_user('reviewer_1', 'reviewer_1@test.com', 'password')
        self.reviewers = Group.objects.create(name='iotd_reviewers')
        self.reviewers.user_set.add(self.reviewer)

        self.judges = Group.objects.create(name = 'iotd_judges')

        self.user = User.objects.create_user('user', 'user@test.com', 'password')
        self.client.login(username='user', password='password')
        self.client.post(
            reverse_lazy('image_upload_process'),
            {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
            follow=True)
        self.client.logout()
        self.image = Image.objects_including_wip.first()

        # Approve the image and set a title
        self.image.moderator_decision = 1
        self.image.title = "IOTD TEST IMAGE"
        self.image.data_source = "BACKYARD"
        self.image.save()

    def tearDown(self):
        self.submitters.delete()
        self.submitter.delete()

        self.reviewers.delete()
        self.reviewer.delete()

        self.judges.delete()

        self.image.delete()
        self.user.delete()

    def test_top_picks_data_source_filter(self):
        IotdSubmission.objects.create(submitter=self.submitter, image=self.image)
        IotdVote.objects.create(reviewer=self.reviewer, image=self.image)

        response = self.client.get(reverse_lazy('top_picks'))
        self.assertContains(response, self.image.title)

        response = self.client.get(reverse_lazy('top_picks') + '?source=backyard')
        self.assertContains(response, self.image.title)

        response = self.client.get(reverse_lazy('top_picks') + '?source=traveller')
        self.assertNotContains(response, self.image.title)

        self.image.data_source = 'TRAVELLER'
        self.image.save()
        response = self.client.get(reverse_lazy('top_picks') + '?source=traveller')
        self.assertContains(response, self.image.title)
        response = self.client.get(reverse_lazy('top_picks') + '?source=backyard')
        self.assertNotContains(response, self.image.title)

        self.image.data_source = 'OWN_REMOTE'
        self.image.save()
        response = self.client.get(reverse_lazy('top_picks') + '?source=own-remote')
        self.assertContains(response, self.image.title)
        response = self.client.get(reverse_lazy('top_picks') + '?source=traveller')
        self.assertNotContains(response, self.image.title)

        self.image.data_source = 'AMATEUR_HOSTING'
        self.image.save()
        response = self.client.get(reverse_lazy('top_picks') + '?source=amateur-hosting')
        self.assertContains(response, self.image.title)
        response = self.client.get(reverse_lazy('top_picks') + '?source=own-remote')
        self.assertNotContains(response, self.image.title)

        self.image.data_source = 'PUBLIC_AMATEUR_DATA'
        self.image.save()
        response = self.client.get(reverse_lazy('top_picks') + '?source=public-amateur-data')
        self.assertContains(response, self.image.title)
        response = self.client.get(reverse_lazy('top_picks') + '?source=amateur-hosting')
        self.assertNotContains(response, self.image.title)

        self.image.data_source = 'PRO_DATA'
        self.image.save()
        response = self.client.get(reverse_lazy('top_picks') + '?source=pro-data')
        self.assertContains(response, self.image.title)
        response = self.client.get(reverse_lazy('top_picks') + '?source=public-amateur-data')
        self.assertNotContains(response, self.image.title)
