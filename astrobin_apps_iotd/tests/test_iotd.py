from datetime import datetime, timedelta, date

import simplejson as json
from bs4 import BeautifulSoup as BS
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings

from astrobin.enums import SubjectType
from astrobin.tests.generators import Generators
from astrobin_apps_groups.models import Group as AstroBinGroup
from astrobin_apps_iotd.models import *
from astrobin_apps_iotd.services import IotdService


@override_settings(
    IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(days=365)
)
class IotdTest(TestCase):

    def setUp(self):
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


    # Models

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_submission_model(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        submission = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)
        self.assertEqual(submission.submitter, self.submitter_1)
        self.assertEqual(submission.image, self.image)

        self.image.published = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(hours=1)
        self.image.save()

        IotdService().update_top_pick_nomination_archive()

        # Badge is not present with just one submission
        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertNotContains(response, 'top-pick-nomination-badge')

        # Image is not in Top Picks Nominations page with just one vote
        response = self.client.get(reverse_lazy('top_pick_nominations'))
        self.assertNotContains(response, self.image.title)
        cache.clear()

        self.image.published = datetime.now()
        self.image.save()

        IotdSubmission.objects.create(
            submitter=self.submitter_2,
            image=self.image)

        self.image.published = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(hours=1)
        self.image.save()

        IotdService().update_top_pick_nomination_archive()

        # Badge is present
        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertContains(response, 'top-pick-nomination-badge')

        # Image is in Top Picks Nominations page
        response = self.client.get(reverse_lazy('top_pick_nominations'))
        self.assertContains(response, self.image.title)
        cache.clear()

        # Image cannot be submitted again
        with self.assertRaisesRegex(ValidationError, "already exists"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)

        # Test max daily
        with self.assertRaisesRegex(ValidationError, "already submitted.*today"):
            image2 = Image.objects.create(user=self.user)
            with self.settings(IOTD_SUBMISSION_MAX_PER_DAY=1):
                IotdSubmission.objects.create(
                    submitter=self.submitter_1,
                    image=image2)

    def test_submission_model_user_must_be_submitter(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        with self.assertRaisesRegex(ValidationError, "not a member"):
            IotdSubmission.objects.create(
                submitter=self.user,
                image=self.image)

    def test_submission_model_image_must_be_recent(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.image.published = \
            datetime.now() - \
            timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS + 1)
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "published more than"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)

    def test_submission_model_image_must_be_public(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.image.published = datetime.now()
        self.image.is_wip = True
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "staging area"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.is_wip = False
        self.image.save(keep_deleted=True)

    def test_submission_model_image_owner_must_not_be_excluded_from_cometitions(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.image.user.userprofile.exclude_from_competitions = True
        self.image.user.userprofile.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "excluded from competitions"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user.userprofile.exclude_from_competitions = False
        self.image.user.userprofile.save(keep_deleted=True)

    def test_submission_model_image_owner_must_not_be_banned_from_cometitions(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.image.user.userprofile.banned_from_competitions = datetime.now()
        self.image.user.userprofile.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "banned from competitions"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user.userprofile.banned_from_competitions = None
        self.image.user.userprofile.save(keep_deleted=True)

    def test_submission_model_cannot_submit_own_image(self):
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.image.user = self.submitter_1
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "your own image"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user = self.user
        self.image.save(keep_deleted=True)

    def test_submission_model_cannot_submit_image_of_free_account(self):
        with self.assertRaisesRegex(ValidationError, "a Free membership"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
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
        with self.assertRaisesRegex(ValidationError, "already been an IOTD"):
            IotdSubmission.objects.create(
                submitter=self.submitter_2,
                image=self.image)

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

    def test_submission_model_cannot_submit_image_that_was_dismissed(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        IotdDismissedImage.objects.create(image=self.image, user=self.submitter_1)
        with self.assertRaisesRegex(ValidationError, "you already dismissed"):
            IotdSubmission.objects.create(submitter=self.submitter_1, image=self.image)

    @override_settings(IOTD_MAX_DISMISSALS=3)
    def test_submission_model_cannot_submit_image_that_was_dismissed_3_times(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        IotdDismissedImage.objects.create(image=self.image, user=Generators.user(groups=['iotd_submitters']))
        IotdDismissedImage.objects.create(image=self.image, user=Generators.user(groups=['iotd_submitters']))
        IotdDismissedImage.objects.create(image=self.image, user=Generators.user(groups=['iotd_submitters']))
        with self.assertRaisesRegex(ValidationError, " has been dismissed by 3 members"):
            IotdSubmission.objects.create(submitter=self.submitter_1, image=self.image)

    def test_vote_model_user_must_be_reviewer(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        with self.assertRaisesRegex(ValidationError, "not a member"):
            IotdVote.objects.create(
                reviewer=self.user,
                image=self.image)

    def test_vote_model_image_must_have_been_submitted(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        with self.assertRaisesRegex(ValidationError, "not been submitted"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=self.image)

    def test_vote_model_cannot_vote_image_by_free_account(self):
        with self.assertRaisesRegex(ValidationError, "a Free membership"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1)
    def test_vote_model_submission_must_be_within_window(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        submission_1 = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)

        IotdSubmission.objects.filter(pk=submission_1.pk).update(
            date= \
                datetime.now() - \
                timedelta(settings.IOTD_REVIEW_WINDOW_DAYS + 1))

        with self.assertRaisesRegex(ValidationError, "in the review queue for more than"):
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
        with self.assertRaisesRegex(ValidationError, "staging area"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=submission_1.image)
        self.image.is_wip = False
        self.image.save(keep_deleted=True)

    def test_vote_model_image_owner_must_not_be_excluded_from_competitions(self):
        self.image.user.userprofile.exclude_from_competitions = True
        self.image.user.userprofile.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "excluded from competitions"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user.userprofile.exclude_from_competitions = False
        self.image.user.userprofile.save(keep_deleted=True)

    def test_vote_model_image_owner_must_not_be_banned_from_competitions(self):
        self.image.user.userprofile.banned_from_competitions = datetime.now()
        self.image.user.userprofile.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "banned from competitions"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user.userprofile.banned_from_competitions = None
        self.image.user.userprofile.save(keep_deleted=True)

    def test_vote_model_cannot_vote_own_image(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        submission_1 = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)

        self.image.user = self.reviewer_1
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "your own image"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=submission_1.image)
        self.image.user = self.user
        self.image.save(keep_deleted=True)

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1)
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

    def test_vote_model_cannot_vote_image_that_was_dismissed(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        IotdSubmission.objects.create(submitter=self.submitter_1, image=self.image)
        IotdDismissedImage.objects.create(image=self.image, user=self.reviewer_1)
        with self.assertRaisesRegex(ValidationError, "you already dismissed"):
            IotdVote.objects.create(reviewer=self.reviewer_1, image=self.image)

    @override_settings(IOTD_MAX_DISMISSALS=3)
    def test_vote_model_cannot_vote_image_that_was_dismissed_3_times(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")
        IotdSubmission.objects.create(submitter=self.submitter_1, image=self.image)
        IotdDismissedImage.objects.create(image=self.image, user=Generators.user(groups=['iotd_submitters']))
        IotdDismissedImage.objects.create(image=self.image, user=Generators.user(groups=['iotd_submitters']))
        IotdDismissedImage.objects.create(image=self.image, user=Generators.user(groups=['iotd_submitters']))
        with self.assertRaisesRegex(ValidationError, " has been dismissed by 3 members"):
            IotdVote.objects.create(reviewer=self.reviewer_1, image=self.image)

    def test_vote_model_cannot_vote_own_submission(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        submission_1 = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)

        self.submitters.user_set.add(self.reviewer_1)
        submission_1.submitter = self.reviewer_1
        submission_1.save()
        with self.assertRaisesRegex(ValidationError, "your own submission"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=submission_1.image)
        self.submitters.user_set.remove(self.reviewer_1)
        submission_1.submitter = self.submitter_1
        submission_1.save()

    @override_settings(
        IOTD_SUBMISSION_MIN_PROMOTIONS=2,
        IOTD_REVIEW_MIN_PROMOTIONS=2,
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(365),
    )
    def test_vote_model(self):
        Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        submission_1 = IotdSubmission.objects.create(
            submitter=self.submitter_1,
            image=self.image)

        IotdSubmission.objects.create(
            submitter=self.submitter_2,
            image=self.image)

        vote = IotdVote.objects.create(
            reviewer=self.reviewer_1,
            image=submission_1.image)
        self.assertEqual(vote.reviewer, self.reviewer_1)
        self.assertEqual(vote.image, submission_1.image)

        self.image.published = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS) - timedelta(hours=1)
        self.image.save()

        IotdService().update_top_pick_archive()

        # Badge is not present with just one vote
        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertNotContains(response, 'top-pick-badge')

        # Image is not in Top Picks page with just one vote
        response = self.client.get(reverse_lazy('top_picks'))
        self.assertNotContains(response, self.image.title)
        cache.clear()

        self.image.published = datetime.now()
        self.image.save()

        IotdVote.objects.create(
            reviewer=self.reviewer_2,
            image=submission_1.image)

        self.image.published = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS) - timedelta(hours=1)
        self.image.save()

        IotdService().update_top_pick_archive()

        # Badge is present
        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertContains(response, 'top-pick-badge')

        # Image is in Top Picks page
        response = self.client.get(reverse_lazy('top_picks'))
        self.assertContains(response, self.image.title)
        cache.clear()

        iotd = Iotd.objects.create(
            judge=self.judge_1,
            image=self.image,
            date=datetime.now().date() + timedelta(1))

        IotdService().update_top_pick_archive()

        # Badge is still present if image is future IOTD
        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertContains(response, 'top-pick-badge')

        # Image is still in Top Picks page
        response = self.client.get(reverse_lazy('top_picks'))
        self.assertContains(response, self.image.title)
        cache.clear()

        # Badge is gone if image is present IOTD

        Iotd.objects.filter(pk=iotd.pk).update(date=datetime.now().date())
        IotdService().update_top_pick_archive()

        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertNotContains(response, 'top-pick-badge')

        # Image is still from Top Picks page. It did earn that badge after all
        response = self.client.get(reverse_lazy('top_picks'))
        self.assertContains(response, self.image.title)
        cache.clear()

        # Badge is gone is image is past IOTD
        Iotd.objects.filter(pk=iotd.pk).update(date=datetime.now().date() - timedelta(1))
        IotdService().update_top_pick_archive()

        response = self.client.get(reverse_lazy('image_detail', args=(self.image.get_id(),)))
        self.assertNotContains(response, 'top-pick-badge')

        # Image is still not gone from Top Picks page
        response = self.client.get(reverse_lazy('top_picks'))
        self.assertContains(response, self.image.title)
        cache.clear()

        iotd.delete()

        # Image must not be past IOTD
        iotd = Iotd.objects.create(
            judge=self.judge_1,
            image=self.image,
            date=datetime.now().date() - timedelta(1))
        with self.assertRaisesRegex(ValidationError, "already been an IOTD"):
            IotdVote.objects.create(
                reviewer=self.reviewer_2,
                image=self.image)
        iotd.delete()

        # Cannot vote again for the same
        with self.assertRaisesRegex(ValidationError, "already exists"):
            IotdVote.objects.create(
                reviewer=self.reviewer_1,
                image=submission_1.image)

        # Test max daily
        image2 = Image.objects.create(user=self.user)
        submission_2 = IotdSubmission.objects.create(
            submitter=self.submitter_2,
            image=image2)
        with self.assertRaisesRegex(ValidationError, "already voted.*today"):
            with self.settings(
                    IOTD_SUBMISSION_MIN_PROMOTIONS=1,
                    IOTD_REVIEW_MIN_PROMOTIONS=1,
                    IOTD_REVIEW_MAX_PER_DAY=1
            ):
                IotdVote.objects.create(
                    reviewer=self.reviewer_1,
                    image=submission_2.image)

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_iotd_model(self):
        # User must be judge
        with self.assertRaisesRegex(ValidationError, "not a member"):
            Iotd.objects.create(
                judge=self.user,
                image=self.image,
                date=datetime.now().date())

        # Cannot elect an image authored by:
        # - a free account
        with self.assertRaisesRegex(ValidationError, "a Free membership"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)

        image_author_us = Generators.premium_subscription(self.image.user, "AstroBin Ultimate 2020+")

        # Image must have been voted
        with self.assertRaisesRegex(ValidationError, "has not been voted"):
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
        with self.assertRaisesRegex(ValidationError, "in the review queue for more than"):
            Iotd.objects.create(
                judge=self.judge_1,
                image=vote_1.image)
        IotdVote.objects.filter(pk=vote_1.pk).update(
            date=datetime.now())

        # Image must not be WIP
        self.image.is_wip = True
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "staging area"):
            Iotd.objects.create(
                judge=self.judge_1,
                image=self.image)
        self.image.is_wip = False
        self.image.save(keep_deleted=True)

        # Image owner must not be excluded from competitions
        self.image.user.userprofile.exclude_from_competitions = True
        self.image.user.userprofile.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "excluded from competitions"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user.userprofile.exclude_from_competitions = False
        self.image.user.userprofile.save(keep_deleted=True)

        # Image owner must not be banned from competitions
        self.image.user.userprofile.banned_from_competitions = datetime.now()
        self.image.user.userprofile.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "banned from competitions"):
            IotdSubmission.objects.create(
                submitter=self.submitter_1,
                image=self.image)
        self.image.user.userprofile.banned_from_competitions = None
        self.image.user.userprofile.save(keep_deleted=True)

        # Cannot elect own image
        self.image.user = self.judge_1
        self.image.save(keep_deleted=True)
        with self.assertRaisesRegex(ValidationError, "your own image"):
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
        with self.assertRaisesRegex(ValidationError, "your own submission"):
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
        with self.assertRaisesRegex(ValidationError, "you voted for"):
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
        with self.assertRaisesRegex(ValidationError, "already been an IOTD"):
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
            with self.assertRaisesRegex(ValidationError, "already scheduled"):
                Iotd.objects.create(
                    judge=self.judge_1,
                    image=image3)

    # Views

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

    @override_settings(
        IOTD_SUBMISSION_MIN_PROMOTIONS=1,
        IOTD_REVIEW_MIN_PROMOTIONS=1,
        PREMIUM_RESTRICTS_IOTD=False
    )
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
