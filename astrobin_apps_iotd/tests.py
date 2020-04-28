from datetime import datetime, timedelta, date

import simplejson as json
from beautifulsoupselect import BeautifulSoupSelect as BSS
from bs4 import BeautifulSoup as BS
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from mock import patch

from astrobin.enums import SubjectType
from astrobin.tests.generators import Generators
from astrobin_apps_groups.models import Group as AstroBinGroup
from astrobin_apps_iotd.models import *


class IotdTest(TestCase):
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def setUp(self, retrieve_primary_thumbnails):
        self.submitter_1 = User.objects.create_user('submitter_1', 'submitter_1@test.com', 'password')
        self.submitter_2 = User.objects.create_user('submitter_2', 'submitter_2@test.com', 'password')
        self.submitter_3 = User.objects.create_user('submitter_3', 'submitter_3@test.com', 'password')
        self.submitters = Group.objects.create(name='iotd_submitters')
        self.submitters.user_set.add(self.submitter_1, self.submitter_2, self.submitter_3)

        self.reviewer_1 = User.objects.create_user('reviewer_1', 'reviewer_1@test.com', 'password')
        self.reviewer_2 = User.objects.create_user('reviewer_2', 'reviewer_2@test.com', 'password')
        self.reviewer_3 = User.objects.create_user('reviewer_3', 'reviewer_3@test.com', 'password')
        self.reviewers = Group.objects.create(name='iotd_reviewers')
        self.reviewers.user_set.add(self.reviewer_1, self.reviewer_2, self.reviewer_3)

        self.judge_1 = User.objects.create_user('judge_1', 'judge_1@test.com', 'password')
        self.judge_2 = User.objects.create_user('judge_2', 'judge_2@test.com', 'password')
        self.judges = Group.objects.create(name='iotd_judges')
        self.judges.user_set.add(self.judge_1, self.judge_2)

        self.user = User.objects.create_user('user', 'user@test.com', 'password')
        self.client.login(username='user', password='password')
        self.client.post(
            reverse_lazy('image_upload_process'),
            {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
            follow=True)
        self.client.logout()
        self.image = Image.objects_including_wip.first()

        self.image.moderator_decision = 1
        self.image.title = "IOTD TEST IMAGE"
        self.image.subject_type = SubjectType.DEEP_SKY
        self.image.save(keep_deleted=True)

    def tearDown(self):
        self.submitters.delete()
        self.submitter_1.delete()
        self.submitter_2.delete()
        self.submitter_3.delete()

        self.reviewers.delete()
        self.reviewer_1.delete()
        self.reviewer_2.delete()
        self.reviewer_3.delete()

        self.judges.delete()
        self.judge_1.delete()
        self.judge_2.delete()

        self.user.delete()

    # Models

    def test_submission_model(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        submission = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)
        self.assertEqual(submission.submitter, self.submitter_1)
        self.assertEqual(submission.image, self.image)

        # Image cannot be submitted again
        with self.assertRaisesRegexp(ValidationError, "already exists"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)

        # Test max daily
        with self.assertRaisesRegexp(ValidationError, "already submitted.*today"):
            image2 = Image.objects.create(user=self.user)
            with self.settings(IOTD_SUBMISSION_MAX_PER_DAY=1):
                IotdSubmission.objects.create(
                    submitter=self.submitter_1,
                    image=image2)

    def test_submission_model_user_must_be_submitter(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        with self.assertRaisesRegexp(ValidationError, "not a member"):
            IotdSubmission.objects.create(
                submitter=self.user,
                image=self.image)

    def test_submission_model_image_must_be_recent(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.image.published = \
            datetime.now() - \
            timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS + 1)
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegexp(ValidationError, "published more than"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)

    def test_submission_model_image_must_be_public(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.image.published = datetime.now()
        self.image.is_wip = True
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegexp(ValidationError, "staging area"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.is_wip = False
        self.image.save(keep_deleted=True)

    def test_submission_model_image_owner_must_not_excluded_from_cometitions(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.image.user.userprofile.exclude_from_competitions = True
        self.image.user.userprofile.save(keep_deleted=True)
        with self.assertRaisesRegexp(ValidationError, "excluded from competitions"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user.userprofile.exclude_from_competitions = False
        self.image.user.userprofile.save(keep_deleted=True)

    def test_submission_model_cannot_submit_own_image(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.image.user = self.submitter_1
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegexp(ValidationError, "your own image"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user = self.user
        self.image.save(keep_deleted=True)

    def test_submission_model_cannot_submit_image_of_free_account(self):
        with self.assertRaisesRegexp(ValidationError, "a Free membership"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)

    def test_submission_model_image_cannot_be_past_iotd(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")

        submission = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)
        self.assertEqual(submission.submitter, self.submitter_1)
        self.assertEqual(submission.image, self.image)

        vote = IotdVote.objects.create(
            reviewer=self.reviewer_1,
            image=self.image)
        iotd = Iotd.objects.create(
            judge=self.judge_1,
            image=self.image,
            date=datetime.now().date() - timedelta(1))
        with self.assertRaisesRegexp(ValidationError, "already been an IOTD"):
            IotdSubmission.objects.create(
                submitter=self.submitter_2,
                image=self.image)
        vote.delete()
        iotd.delete()

    def test_submission_model_can_submit_image_by_judge(self):
        self.image.user = self.judge_1
        self.image.save(keep_deleted=True)

        Generators.premium_subscription(self.judge_1, "AstroBin Ultimate 2020+")

        try:
            submission = IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        except ValidationError as e:
            self.fail(e)

        self.assertEqual(submission.submitter, self.submitter_1)
        self.assertEqual(submission.image, self.image)

    def test_vote_model_user_must_be_reviewer(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        with self.assertRaisesRegexp(ValidationError, "not a member"):
            IotdVote.objects.create(
                reviewer=self.user,
                image=self.image)

    def test_vote_model_image_must_have_been_submitted(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        with self.assertRaisesRegexp(ValidationError, "not been submitted"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=self.image)

    def test_vote_model_cannot_vote_image_by_free_account(self):
        with self.assertRaisesRegexp(ValidationError, "a Free membership"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)

    def test_vote_model_submission_must_be_within_window(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        submission_1 = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)

        IotdSubmission.objects.filter(pk=submission_1.pk).update(
            date= \
                datetime.now() - \
                timedelta(settings.IOTD_REVIEW_WINDOW_DAYS + 1))

        with self.assertRaisesRegexp(ValidationError, "in the submission queue for more than"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=submission_1.image)

    def test_vote_model_image_must_be_public(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        submission_1 = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)

        self.image.is_wip = True
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegexp(ValidationError, "staging area"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=submission_1.image)
        self.image.is_wip = False
        self.image.save(keep_deleted=True)

    def test_vote_model_image_owner_must_not_be_excluded_from_competitions(self):
        self.image.user.userprofile.exclude_from_competitions = True
        self.image.user.userprofile.save(keep_deleted=True)
        with self.assertRaisesRegexp(ValidationError, "excluded from competitions"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user.userprofile.exclude_from_competitions = False
        self.image.user.userprofile.save(keep_deleted=True)

    def test_vote_model_cannot_vote_own_image(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        submission_1 = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)

        self.image.user = self.reviewer_1
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegexp(ValidationError, "your own image"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=submission_1.image)
        self.image.user = self.user
        self.image.save(keep_deleted=True)

    def test_vote_model_can_vote_image_by_judge(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)

        self.image.user = self.judge_1
        self.image.save(keep_deleted=True)
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        try:
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=self.image)
        except ValidationError as e:
            self.fail(e)
        self.image.user = self.user
        self.image.save(keep_deleted=True)

    def test_vote_model_cannot_vote_own_submission(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        submission_1 = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)

        self.submitters.user_set.add(self.reviewer_1)
        submission_1.submitter = self.reviewer_1
        submission_1.save()
        with self.assertRaisesRegexp(ValidationError, "your own submission"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=submission_1.image)
        self.submitters.user_set.remove(self.reviewer_1)
        submission_1.submitter = self.submitter_1
        submission_1.save()

    def test_vote_model(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        submission_1 = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)

        vote = IotdVote.objects.create(
            reviewer=self.reviewer_1,
            image=submission_1.image)
        self.assertEqual(vote.reviewer, self.reviewer_1)
        self.assertEqual(vote.image, submission_1.image)

        # Badge is present
        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertContains(response, 'top-pick-badge')

        # Image is in Top Picks page
        response = self.client.get(reverse_lazy('top_picks'))
        self.assertContains(response, self.image.title)
        cache.clear()

        # Badge is still present if image is future IOTD
        iotd = Iotd.objects.create(
            judge=self.judge_1,
            image=self.image,
            date=datetime.now().date() + timedelta(1))
        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertContains(response, 'top-pick-badge')

        # Image is still in Top Picks page
        response = self.client.get(reverse_lazy('top_picks'))
        self.assertContains(response, self.image.title)
        cache.clear()

        # Badge is gone if image is present IOTD

        Iotd.objects.filter(pk=iotd.pk).update(date=datetime.now().date())
        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertNotContains(response, 'top-pick-badge')

        # Image is gone from Top Picks page
        response = self.client.get(reverse_lazy('top_picks'))
        self.assertNotContains(response, self.image.title)
        cache.clear()

        # Badge is gone is image is past IOTD
        Iotd.objects.filter(pk=iotd.pk).update(date=datetime.now().date() - timedelta(1))
        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertNotContains(response, 'top-pick-badge')

        # Image is still gone from Top Picks page
        response = self.client.get(reverse_lazy('top_picks'))
        self.assertNotContains(response, self.image.title)
        cache.clear()

        iotd.delete()

        # Image must not be past IOTD
        iotd = Iotd.objects.create(
            judge=self.judge_1,
            image=self.image,
            date=datetime.now().date() - timedelta(1))
        with self.assertRaisesRegexp(ValidationError, "already been an IOTD"):
            IotdVote.objects.create(
                reviewer=self.reviewer_2,
                image=self.image)
        iotd.delete()

        # Cannot vote again for the same
        with self.assertRaisesRegexp(ValidationError, "already exists"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=submission_1.image)

        # Test max daily
        image2 = Image.objects.create(user=self.user)
        submission_2 = IotdSubmission.objects.create(
            submitter=self.submitter_2,
            image=image2)
        with self.assertRaisesRegexp(ValidationError, "already voted.*today"):
            with self.settings(IOTD_REVIEW_MAX_PER_DAY=1):
                IotdVote.objects.create(
                    reviewer=self.reviewer_1,
                    image=submission_2.image)

        submission_1.delete()
        submission_2.delete()
        image2.delete()

    def test_iotd_model(self):
        # User must be judge
        with self.assertRaisesRegexp(ValidationError, "not a member"):
            Iotd.objects.create(
                judge=self.user,
                image=self.image,
                date=datetime.now().date())

        # Cannot elect an image authored by:
        # - a free account
        with self.assertRaisesRegexp(ValidationError, "a Free membership"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)

        image_author_us = Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        # Image must have been voted
        with self.assertRaisesRegexp(ValidationError, "has not been voted"):
            Iotd.objects.create(
                judge=self.judge_1,
                image=self.image,
                date=datetime.now().date())
        submission_1 = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)
        vote_1 = IotdVote.objects.create(
            reviewer=self.reviewer_1,
            image=self.image)

        # Vote must be within window
        IotdVote.objects.filter(pk=vote_1.pk).update(
            date= \
                datetime.now() - \
                timedelta(settings.IOTD_JUDGEMENT_WINDOW_DAYS + 1))
        with self.assertRaisesRegexp(ValidationError, "in the review queue for more than"):
            Iotd.objects.create(
                judge=self.judge_1,
                image=vote_1.image)
        IotdVote.objects.filter(pk=vote_1.pk).update(
            date=datetime.now())

        # Image must not be WIP
        self.image.is_wip = True
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegexp(ValidationError, "staging area"):
            Iotd.objects.create(
                judge=self.judge_1,
                image=self.image)
        self.image.is_wip = False
        self.image.save(keep_deleted=True)

        # Image owner must not be excluded from competitions
        self.image.user.userprofile.exclude_from_competitions = True
        self.image.user.userprofile.save(keep_deleted=True)
        with self.assertRaisesRegexp(ValidationError, "excluded from competitions"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user.userprofile.exclude_from_competitions = False
        self.image.user.userprofile.save(keep_deleted=True)

        # Cannot elect own image
        self.image.user = self.judge_1
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegexp(ValidationError, "your own image"):
            Iotd.objects.create(
                judge=self.judge_1,
                image=self.image)
        self.image.user = self.user
        self.image.save(keep_deleted=True)

        # Can elect an image authored by a judge
        self.image.user = self.judge_2
        self.image.save(keep_deleted=True)
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        try:
            iotd = Iotd.objects.create(
                judge=self.judge_1,
                image=self.image,
                date=date.today())
            iotd.delete()
        except ValidationError as e:
            self.fail(e)
        self.image.user = self.user
        self.image.save(keep_deleted=True)

        # Cannot elect own submission
        self.submitters.user_set.add(self.judge_1)
        submission_1.submitter = self.judge_1
        submission_1.save()
        with self.assertRaisesRegexp(ValidationError, "your own submission"):
            Iotd.objects.create(
                judge=self.judge_1,
                image=submission_1.image)
        self.submitters.user_set.remove(self.judge_1)
        submission_1.submitter = self.submitter_1
        submission_1.save()

        # Cannot elect own voted image
        self.reviewers.user_set.add(self.judge_1)
        vote_1.reviewer = self.judge_1
        vote_1.save()
        with self.assertRaisesRegexp(ValidationError, "you voted for"):
            Iotd.objects.create(
                judge=self.judge_1,
                image=vote_1.image)
        self.reviewers.user_set.remove(self.judge_1)
        vote_1.reviewer = self.reviewer_1
        vote_1.save()

        # All OK
        iotd = Iotd.objects.create(
            judge=self.judge_1,
            image=self.image,
            date=datetime.now().date())
        self.assertEqual(iotd.judge, self.judge_1)
        self.assertEqual(iotd.image, self.image)

        # Badge is present
        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertContains(response, 'iotd-ribbon')

        # Image must not be past IOTD
        with self.assertRaisesRegexp(ValidationError, "already been an IOTD"):
            Iotd.objects.create(
                judge=self.judge_1,
                image=self.image)

        # No more than IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE already scheduled
        with self.settings(
                IOTD_JUDGEMENT_MAX_PER_DAY=3,
                IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE=1):
            image2 = Image.objects.create(user=self.user)
            submission_2 = IotdSubmission.objects.create(
                submitter=self.submitter_2,
                image=image2)
            vote_2 = IotdVote.objects.create(
                reviewer=self.reviewer_2,
                image=image2)
            Iotd.objects.create(
                judge=self.judge_1,
                image=image2,
                date=datetime.now().date() + timedelta(1))

            image3 = Image.objects.create(user=self.user)
            submission_3 = IotdSubmission.objects.create(
                submitter=self.submitter_3,
                image=image3)
            vote_3 = IotdVote.objects.create(
                reviewer=self.reviewer_3,
                image=image3)
            with self.assertRaisesRegexp(ValidationError, "already scheduled"):
                Iotd.objects.create(
                    judge=self.judge_1,
                    image=image3)

        iotd.delete()
        vote_1.delete()
        vote_2.delete()
        vote_3.delete()
        submission_1.delete()
        submission_2.delete()
        submission_3.delete()
        image_author_us.delete()

    # Views

    @override_settings(PREMIUM_RESTRICTS_IOTD=False)
    def test_submission_queue_view(self):
        url = reverse_lazy('iotd_submission_queue')

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Only submitters allowed
        self.client.login(username='user', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='submitter_1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="used">0</span>', html=True)

        # Check that images from a free user are not rendered
        response = self.client.get(url)
        self.assertNotContains(response, 'data-id="%s"' % self.image.pk)

        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        response = self.client.get(url)
        self.assertContains(response, 'data-id="%s"' % self.image.pk)

        # Check for may-not-select class
        # self.image.user = self.submitter_1
        # self.image.save(keep_deleted=True)
        # response = self.client.get(url)
        # bs = BS(response.content, "lxml")
        # self.assertEqual(len(bs.select('.iotd-queue-item.may-not-select')), 1)
        # self.submitters.user_set.remove(self.reviewer_1)
        # self.image.user = self.user
        # self.image.save(keep_deleted=True)

        # Check that non-moderated (or spam) images are not rendered
        self.image.moderator_decision = 0
        self.image.save(keep_deleted=True)
        submission = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)
        response = self.client.get(url)
        self.assertNotContains(response, 'data-id="%s"' % self.image.pk)
        submission.delete()

        self.image.moderator_decision = 2
        self.image.save(keep_deleted=True)
        submission = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)
        response = self.client.get(url)
        self.assertNotContains(response, 'data-id="%s"' % self.image.pk)
        submission.delete()

        self.image.moderator_decision = 1
        self.image.save(keep_deleted=True)

        # Images that are too old are not rendered
        self.image.published =\
            datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(minutes=1)
        self.image.save()
        response = self.client.get(url)
        self.assertNotContains(response, 'data-id="%s"' % self.image.pk)

        self.image.published = \
            datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS) + timedelta(minutes=1)
        self.image.save()
        response = self.client.get(url)
        self.assertContains(response, 'data-id="%s"' % self.image.pk)

        # Images by judges are shown here
        Generators.premium_subscription(self.judge_1, "AstroBin Ultimate 2020+")
        self.image.user = self.judge_1
        self.image.save(keep_deleted=True)
        response = self.client.get(url)
        self.assertContains(response, 'data-id="%s"' % self.image.pk)
        self.image.user = self.user
        self.image.save(keep_deleted=True)

        # Check that current or past IOTD is not rendered
        submission = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)
        vote = IotdVote.objects.create(
            reviewer=self.reviewer_1,
            image=self.image)
        iotd = Iotd.objects.create(
            judge=self.judge_1,
            image=self.image,
            date=datetime.now().date())
        response = self.client.get(url)
        self.assertNotContains(response, 'data-id="%s"' % self.image.pk)

        # Future IOTD should render tho
        Iotd.objects.filter(image=self.image).update(
            date=datetime.now().date() + timedelta(1))
        response = self.client.get(url)
        self.assertContains(response, 'data-id="%s"' % self.image.pk)

        submission.delete()
        vote.delete()
        iotd.delete()

    @override_settings(PREMIUM_RESTRICTS_IOTD=False)
    def test_toggle_submission_ajax_view(self):
        url = reverse_lazy('iotd_toggle_submission_ajax', kwargs={'pk': self.image.pk})

        # Login required
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # Only submitters allowed
        self.client.login(username='user', password='password')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # GET not allowed
        self.client.login(username='submitter_1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Only AJAX allowed
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        # All OK
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('submission' in json.loads(response.content))
        self.assertEqual(json.loads(response.content)['used_today'], 1)
        self.assertFalse('error' in json.loads(response.content))
        self.assertEqual(IotdSubmission.objects.count(), 1)

        # Toggle off
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['used_today'], 0)
        self.assertFalse('submission' in json.loads(response.content))
        self.assertFalse('error' in json.loads(response.content))
        self.assertEqual(IotdSubmission.objects.count(), 0)

        # You can still toggle off if you reached your max
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(IotdSubmission.objects.count(), 1)
        with self.settings(IOTD_SUBMISSION_MAX_PER_DAY=1):
            response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(IotdSubmission.objects.count(), 0)

    @override_settings(PREMIUM_RESTRICTS_IOTD=False)
    def test_review_queue_view(self):
        url = reverse_lazy('iotd_review_queue')

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Only reviewers allowed
        self.client.login(username='submitter_1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='reviewer_1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="used">0</span>', html=True)

        # Check that images are rendered
        submission_1 = IotdSubmission.objects.create(submitter=self.submitter_1, image=self.image)
        response = self.client.get(url)
        self.assertContains(response, 'data-id="%s"' % self.image.pk)

        # Check that multiple submissions for the same image result in one single image rendered
        submission_2 = IotdSubmission.objects.create(submitter=self.submitter_2, image=self.image)
        response = self.client.get(url)
        bss = BSS(response.content)
        self.assertEqual(len(bss('.astrobin-image-container')), 1)

        # Check for count badge
        self.assertEqual(bss('.iotd-queue-item .badge')[0].attrMap['title'], '2')
        submission_2.delete()

        # Check for may-not-select class
        submission_1.submitter = self.reviewer_1
        self.submitters.user_set.add(self.reviewer_1)
        submission_1.save()
        response = self.client.get(url)
        bs = BS(response.content, "lxml")
        self.assertEqual(len(bs.select('.iotd-queue-item.may-not-select')), 1)
        self.submitters.user_set.remove(self.reviewer_1)
        submission_1.submitter = self.submitter_1
        submission_1.save()

        # Check that current or past IOTD is not rendered
        vote = IotdVote.objects.create(
            reviewer=self.reviewer_1,
            image=self.image)
        iotd = Iotd.objects.create(
            judge=self.judge_1,
            image=self.image,
            date=datetime.now().date())
        response = self.client.get(url)
        self.assertNotContains(response, 'data-id="%s"' % self.image.pk)

        # Future IOTD should render tho
        Iotd.objects.filter(image=self.image).update(
            date=datetime.now().date() + timedelta(1))
        response = self.client.get(url)
        self.assertContains(response, 'data-id="%s"' % self.image.pk)

        # Images by judges are shown here
        self.image.user = self.judge_1
        self.image.save(keep_deleted=True)
        response = self.client.get(url)
        self.assertContains(response, 'data-id="%s"' % self.image.pk)
        self.image.user = self.user
        self.image.save(keep_deleted=True)

        submission_1.delete()
        vote.delete()
        iotd.delete()

    @override_settings(PREMIUM_RESTRICTS_IOTD=False)
    def test_toggle_vote_ajax_view(self):
        url = reverse_lazy('iotd_toggle_vote_ajax', kwargs={'pk': self.image.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Only reviewers allowed
        self.client.login(username='submitter_1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # GET not allowed
        self.client.login(username='reviewer_1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Only AJAX allowed
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        # All OK
        submission = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('vote' in json.loads(response.content))
        self.assertEqual(json.loads(response.content)['used_today'], 1)
        self.assertFalse('error' in json.loads(response.content))
        self.assertEqual(IotdVote.objects.count(), 1)

        # Toggle off
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['used_today'], 0)
        self.assertFalse('vote' in json.loads(response.content))
        self.assertFalse('error' in json.loads(response.content))
        self.assertEqual(IotdVote.objects.count(), 0)

        # You can still toggle off if you reached your max
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(IotdVote.objects.count(), 1)
        with self.settings(IOTD_REVIEW_MAX_PER_DAY=1):
            response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(IotdVote.objects.count(), 0)

    @override_settings(PREMIUM_RESTRICTS_IOTD=False)
    def test_judgement_queue_view(self):
        url = reverse_lazy('iotd_judgement_queue')

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Only judges allowed
        self.client.login(username='reviewer_1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='judge_1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span class="used">0</span>', html=True)

        # Check that images are rendered
        submission_1 = IotdSubmission.objects.create(submitter=self.submitter_1, image=self.image)
        vote_1 = IotdVote.objects.create(reviewer=self.reviewer_1, image=self.image)
        response = self.client.get(url)
        self.assertContains(response, 'data-id="%s"' % self.image.pk)

        # Check that multiple votes for the same image result in one single image rendered
        vote_2 = IotdVote.objects.create(reviewer=self.reviewer_2, image=self.image)
        response = self.client.get(url)
        bss = BSS(response.content)
        self.assertEqual(len(bss('.astrobin-image-container')), 1)

        # Check for count badge
        self.assertEqual(bss('.iotd-queue-item .badge')[0].attrMap['title'], '2')
        vote_2.delete()

        # Check for may-not-select class
        self.reviewers.user_set.add(self.judge_1)
        vote_1.reviewer = self.judge_1
        vote_1.save()
        response = self.client.get(url)
        bs = BS(response.content, "lxml")
        self.assertEqual(len(bs.select('.iotd-queue-item.may-not-select')), 1)
        self.reviewers.user_set.remove(self.judge_1)
        vote_1.reviewer = self.reviewer_1
        vote_1.save()

        # Check that current or past IOTD is not rendered
        iotd = Iotd.objects.create(
            judge=self.judge_1,
            image=self.image,
            date=datetime.now().date())
        response = self.client.get(url)
        self.assertNotContains(response, 'data-id="%s"' % self.image.pk)

        # Future IOTD should render tho
        Iotd.objects.filter(image=self.image).update(
            date=datetime.now().date() + timedelta(1))
        response = self.client.get(url)
        self.assertContains(response, 'data-id="%s"' % self.image.pk)

        # Images by judges are shown here
        self.image.user = self.judge_1
        self.image.save(keep_deleted=True)
        response = self.client.get(url)
        self.assertContains(response, 'data-id="%s"' % self.image.pk)
        self.image.user = self.user
        self.image.save(keep_deleted=True)

        submission_1.delete()
        vote_1.delete()
        iotd.delete()

    @override_settings(PREMIUM_RESTRICTS_IOTD=False)
    def test_toggle_judgement_ajax_view(self):
        url = reverse_lazy('iotd_toggle_judgement_ajax', kwargs={'pk': self.image.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Only judges allowed
        self.client.login(username='reviewer_1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # GET not allowed
        self.client.login(username='judge_1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Only AJAX allowed
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        # IOTD for today
        today = datetime.now().date()
        submission = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)
        vote = IotdVote.objects.create(
            reviewer=self.reviewer_1,
            image=self.image)
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('iotd' in json.loads(response.content))
        self.assertEqual(json.loads(response.content)['used_today'], 1)
        self.assertFalse('error' in json.loads(response.content))
        self.assertEqual(json.loads(response.content)['date'], today.strftime('%m/%d/%Y'))
        self.assertEqual(Iotd.objects.count(), 1)
        iotd = Iotd.objects.all()[0]
        self.assertEqual(iotd.judge, self.judge_1)
        self.assertEqual(iotd.image, self.image)
        self.assertEqual(iotd.date, today)

        # Cannot unelect current IOTD
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('error' in json.loads(response.content))
        self.assertEqual(json.loads(response.content)['error'], "You cannot unelect a past or current IOTD.")
        self.assertTrue('date' in json.loads(response.content))
        self.assertTrue('iotd' in json.loads(response.content))
        self.assertEqual(Iotd.objects.count(), 1)

        # Cannot unelect IOTD elected by another judge
        Iotd.objects.filter(pk=iotd.pk).update(
            judge=self.judge_2,
            date=today + timedelta(1))  # Make it future
        iotd = Iotd.objects.get(pk=iotd.pk)  # sqlite won't do the .update above without this?
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('error' in json.loads(response.content))
        self.assertEqual(json.loads(response.content)['error'], "You cannot unelect an IOTD elected by another judge.")
        self.assertTrue('date' in json.loads(response.content))
        self.assertTrue('iotd' in json.loads(response.content))
        self.assertEqual(Iotd.objects.count(), 1)
        iotd.judge = self.judge_1
        # Keep future date for next test
        iotd.save()

        # Unelect OK
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['used_today'], 0)
        self.assertFalse('error' in json.loads(response.content))
        self.assertFalse('date' in json.loads(response.content))
        self.assertFalse('iotd' in json.loads(response.content))
        self.assertEqual(Iotd.objects.count(), 0)

        # Test IOTD fitting first available slot
        image2 = Image.objects.create(user=self.user)
        submission2 = IotdSubmission.objects.create(submitter=self.submitter_1, image=image2)
        vote2 = IotdVote.objects.create(reviewer=self.reviewer_1, image=image2)

        image3 = Image.objects.create(user=self.user)
        submission3 = IotdSubmission.objects.create(submitter=self.submitter_1, image=image3)
        vote3 = IotdVote.objects.create(reviewer=self.reviewer_1, image=image3)

        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        iotd = Iotd.objects.get(pk=json.loads(response.content)['iotd'])
        self.assertEqual(iotd.date, today)

        with self.settings(
                IOTD_JUDGEMENT_MAX_PER_DAY=4, IOTD_SUBMISSION_MAX_PER_DAY=4,
                IOTD_REVIEW_MAX_PER_DAY=4):
            url = reverse_lazy('iotd_toggle_judgement_ajax', kwargs={'pk': image2.pk})
            response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            iotd2 = Iotd.objects.get(pk=json.loads(response.content)['iotd'])
            self.assertEqual(iotd2.date, today + timedelta(1))

            url = reverse_lazy('iotd_toggle_judgement_ajax', kwargs={'pk': image3.pk})
            response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            iotd3 = Iotd.objects.get(pk=json.loads(response.content)['iotd'])
            self.assertEqual(iotd3.date, today + timedelta(2))

            # Fills a hole
            iotd2.delete()
            url = reverse_lazy('iotd_toggle_judgement_ajax', kwargs={'pk': image2.pk})
            response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            iotd2 = Iotd.objects.get(pk=json.loads(response.content)['iotd'])
            self.assertEqual(iotd2.date, today + timedelta(1))

            image4 = Image.objects.create(user=self.user)
            submission4 = IotdSubmission.objects.create(submitter=self.submitter_1, image=image4)
            vote4 = IotdVote.objects.create(reviewer=self.reviewer_1, image=image4)

        # Test MAX_FUTURE_DAYS cutoff
        with self.settings(IOTD_JUDGEMENT_MAX_FUTURE_DAYS=3):
            url = reverse_lazy('iotd_toggle_judgement_ajax', kwargs={'pk': image4.pk})
            response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertFalse('iotd' in json.loads(response.content))
            self.assertTrue("are already filled" in json.loads(response.content)['error'])
            self.assertEqual(Iotd.objects.count(), 3)

        # Test max daily
        with self.settings(IOTD_JUDGEMENT_MAX_PER_DAY=3):
            url = reverse_lazy('iotd_toggle_judgement_ajax', kwargs={'pk': image4.pk})
            response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertFalse('iotd' in json.loads(response.content))
            self.assertTrue("already elected" in json.loads(response.content)['error'])
            self.assertEqual(Iotd.objects.count(), 3)

        # You can still toggle off if you reached your max
        with self.settings(IOTD_JUDGEMENT_MAX_PER_DAY=3):
            response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(Iotd.objects.count(), 3)

        # No more than IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE already scheduled

        with self.settings(
                IOTD_JUDGEMENT_MAX_PER_DAY=4,
                IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE=1):
            response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertFalse('iotd' in json.loads(response.content))
            self.assertTrue("already scheduled" in json.loads(response.content)['error'])
            self.assertEqual(Iotd.objects.count(), 3)

        # Clean up
        image2.delete()
        image3.delete()
        image4.delete()

        submission.delete()
        submission2.delete()
        submission3.delete()
        submission4.delete()

        vote.delete()
        vote2.delete()
        vote3.delete()
        vote4.delete()

        iotd.delete()
        iotd2.delete()
        iotd3.delete()

    @override_settings(PREMIUM_RESTRICTS_IOTD=False)
    def test_group_sync(self):
        group_creator = User.objects.create_user('group_creator', 'group_creator@test.com', 'password')

        staff_group = AstroBinGroup.objects.create(name='IOTD Staff', creator=group_creator, owner=group_creator,
                                                   category=101)
        submitters_group = AstroBinGroup.objects.create(name='IOTD Submitters', creator=group_creator,
                                                        owner=group_creator, category=101)
        reviewers_group = AstroBinGroup.objects.create(name='IOTD Reviewers', creator=group_creator,
                                                       owner=group_creator, category=101)
        judges_group = AstroBinGroup.objects.create(name='IOTD Judges', creator=group_creator, owner=group_creator,
                                                    category=101)

        staff_group_dj, created = Group.objects.get_or_create(name='iotd_staff')
        self.assertFalse(created)

        content_moderators_group_dj, created = Group.objects.get_or_create(name='content_moderators')
        self.assertFalse(created)

        submitters_group_dj, created = Group.objects.get_or_create(name='iotd_submitters')
        self.assertFalse(created)

        reviewers_group_dj, created = Group.objects.get_or_create(name='iotd_reviewers')
        self.assertFalse(created)

        judges_group_dj, created = Group.objects.get_or_create(name='iotd_judges')
        self.assertFalse(created)

        submitters_group.members.add(self.user)
        self.assertTrue(self.user in submitters_group_dj.user_set.all())
        self.assertTrue(self.user in staff_group_dj.user_set.all())
        self.assertTrue(self.user in content_moderators_group_dj.user_set.all())
        self.assertTrue(self.user in staff_group.members.all())
        submitters_group.members.remove(self.user)
        self.assertFalse(self.user in submitters_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group_dj.user_set.all())
        self.assertFalse(self.user in content_moderators_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group.members.all())
        submitters_group.members.add(self.user)
        submitters_group.members.clear()
        self.assertFalse(self.user in submitters_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group_dj.user_set.all())
        self.assertFalse(self.user in content_moderators_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group.members.all())

        reviewers_group.members.add(self.user)
        self.assertTrue(self.user in reviewers_group_dj.user_set.all())
        self.assertTrue(self.user in staff_group_dj.user_set.all())
        self.assertTrue(self.user in content_moderators_group_dj.user_set.all())
        self.assertTrue(self.user in staff_group.members.all())
        reviewers_group.members.remove(self.user)
        self.assertFalse(self.user in reviewers_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group_dj.user_set.all())
        self.assertFalse(self.user in content_moderators_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group.members.all())
        reviewers_group.members.add(self.user)
        reviewers_group.members.clear()
        self.assertFalse(self.user in reviewers_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group_dj.user_set.all())
        self.assertFalse(self.user in content_moderators_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group.members.all())

        judges_group.members.add(self.user)
        self.assertTrue(self.user in judges_group_dj.user_set.all())
        self.assertTrue(self.user in staff_group_dj.user_set.all())
        self.assertTrue(self.user in content_moderators_group_dj.user_set.all())
        self.assertTrue(self.user in staff_group.members.all())
        judges_group.members.remove(self.user)
        self.assertFalse(self.user in judges_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group_dj.user_set.all())
        self.assertFalse(self.user in content_moderators_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group.members.all())
        judges_group.members.add(self.user)
        judges_group.members.clear()
        self.assertFalse(self.user in judges_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group_dj.user_set.all())
        self.assertFalse(self.user in content_moderators_group_dj.user_set.all())
        self.assertFalse(self.user in staff_group.members.all())

        # Add to two groups and removing from one, user should still be in the
        # collective groups
        submitters_group.members.add(self.user)
        reviewers_group.members.add(self.user)
        reviewers_group.members.remove(self.user)
        self.assertTrue(self.user in staff_group_dj.user_set.all())
        self.assertTrue(self.user in content_moderators_group_dj.user_set.all())
        self.assertTrue(self.user in staff_group.members.all())

        # Same using clear
        submitters_group.members.add(self.user)
        reviewers_group.members.add(self.user)
        reviewers_group.members.clear()
        self.assertTrue(self.user in staff_group_dj.user_set.all())
        self.assertTrue(self.user in content_moderators_group_dj.user_set.all())
        self.assertTrue(self.user in staff_group.members.all())

        # Test management command too

        submitters_group.members.add(self.user)
        submitters_group_dj.user_set.remove(self.user)
        staff_group_dj.user_set.remove(self.user)
        content_moderators_group_dj.user_set.remove(self.user)
        call_command('sync_iotd_groups')
        self.assertTrue(self.user in submitters_group_dj.user_set.all())
        self.assertTrue(self.user in staff_group_dj.user_set.all())
        self.assertTrue(self.user in content_moderators_group_dj.user_set.all())

        submitters_group.members.remove(self.user)
        submitters_group_dj.user_set.add(self.user)
        call_command('sync_iotd_groups')
        self.assertFalse(self.user in submitters_group_dj.user_set.all())

        reviewers_group.members.add(self.user)
        reviewers_group_dj.user_set.remove(self.user)
        staff_group_dj.user_set.remove(self.user)
        content_moderators_group_dj.user_set.remove(self.user)
        call_command('sync_iotd_groups')
        self.assertTrue(self.user in reviewers_group_dj.user_set.all())

        reviewers_group.members.remove(self.user)
        reviewers_group_dj.user_set.add(self.user)
        call_command('sync_iotd_groups')
        self.assertFalse(self.user in reviewers_group_dj.user_set.all())

        judges_group.members.add(self.user)
        judges_group_dj.user_set.remove(self.user)
        staff_group_dj.user_set.remove(self.user)
        content_moderators_group_dj.user_set.remove(self.user)
        call_command('sync_iotd_groups')
        self.assertTrue(self.user in judges_group_dj.user_set.all())
        self.assertTrue(self.user in staff_group_dj.user_set.all())
        self.assertTrue(self.user in content_moderators_group_dj.user_set.all())

        judges_group.members.remove(self.user)
        judges_group_dj.user_set.add(self.user)
        call_command('sync_iotd_groups')
        self.assertFalse(self.user in judges_group_dj.user_set.all())

        # Test non removal from collective groups when a user is in another IOTD group
        submitters_group.members.add(self.user)
        reviewers_group.members.add(self.user)
        reviewers_group.members.remove(self.user)
        reviewers_group_dj.user_set.remove(self.user)
        call_command('sync_iotd_groups')
        self.assertTrue(self.user in staff_group_dj.user_set.all())
        self.assertTrue(self.user in content_moderators_group_dj.user_set.all())

        # Clean up
        group_creator.delete()

        submitters_group.delete()
        reviewers_group.delete()
        judges_group.delete()
        staff_group.delete()

        submitters_group_dj.delete()
        reviewers_group_dj.delete()
        judges_group_dj.delete()
        staff_group_dj.delete()
        content_moderators_group_dj.delete()

    @override_settings(PREMIUM_RESTRICTS_IOTD=False)
    def test_iotd_deleted_images(self):
        """Deleted images should not appear in the IOTD archive"""

        IotdSubmission.objects.create(submitter=self.submitter_1, image=self.image)
        IotdVote.objects.create(reviewer=self.reviewer_1, image=self.image)
        Iotd.objects.create(judge=self.judge_1, image=self.image, date=datetime.now())

        response = self.client.get(reverse_lazy('iotd_archive'))
        self.assertContains(response, self.image.title)

        self.image.delete()

        response = self.client.get(reverse_lazy('iotd_archive'))
        self.assertNotContains(response, self.image.title)

        self.image.undelete()
