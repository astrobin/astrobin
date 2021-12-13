from datetime import date, datetime, timedelta

from django.conf import settings
from django.test import TestCase, override_settings
from mock import PropertyMock, patch

from astrobin.enums import SubjectType
from astrobin.tests.generators import Generators
from astrobin_apps_iotd.models import (
    Iotd, IotdDismissedImage, IotdHiddenImage, IotdQueueSortOrder, IotdStaffMemberSettings, IotdSubmission,
    IotdVote,
)
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.tests.iotd_generators import IotdGenerators
from common.services import DateTimeService


class IotdServiceTest(TestCase):
    def _create_iotd(self, **kwargs):
        judge = kwargs.pop('judge', Generators.user(groups=['iotd_judges']))
        when = kwargs.pop('date', date.today())

        user = Generators.user()
        Generators.premium_subscription(user, 'AstroBin Ultimate 2020+')
        image = Generators.image(user=user)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        return IotdGenerators.iotd(judge=judge, image=image, date=when)

    def test_is_iotd_true(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        self.assertTrue(IotdService().is_iotd(image))

    def test_is_iotd_false(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        self.assertFalse(IotdService().is_iotd(image))

    def test_is_iotd_false_future(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() + timedelta(days=1))

        self.assertFalse(IotdService().is_iotd(image))

    def test_is_iotd_false_excluded(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        image.user.userprofile.exclude_from_competitions = True
        image.user.userprofile.save()

        self.assertFalse(IotdService().is_iotd(image))

    def test_is_top_pick_false_only_one_vote_after_cutoff(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        IotdService().update_top_pick_archive()

        self.assertFalse(IotdService().is_top_pick(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS + 1)
    )
    def test_is_top_pick_true_only_one_vote_before_cutoff(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        image.published = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(1)
        image.save()

        IotdService().update_top_pick_archive()

        self.assertTrue(IotdService().is_top_pick(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_is_top_pick_true(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.vote(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_archive()

        self.assertTrue(IotdService().is_top_pick(image))

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS + 1)
    )
    def test_is_top_pick_false(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_archive()

        self.assertFalse(IotdService().is_top_pick(image))

    def test_is_top_picks_false_already_iotd(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_archive()

        self.assertFalse(IotdService().is_top_pick(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_is_top_picks_true_future_iotd(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() + timedelta(days=1))

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_archive()

        self.assertTrue(IotdService().is_top_pick(image))

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS - 1)
    )
    def test_is_top_pick_nomination_false_only_one_submission_after_cutoff(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        self.assertFalse(IotdService().is_top_pick_nomination(image))

    @override_settings(
        IOTD_SUBMISSION_MIN_PROMOTIONS=2,
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS + 1))
    def test_is_top_pick_nomination_true_only_one_submission_before_cutoff(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)

        image.published = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(minutes=1)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        self.assertTrue(IotdService().is_top_pick_nomination(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_is_top_pick_nomination_true(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        self.assertTrue(IotdService().is_top_pick_nomination(image))

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS - 1)
    )
    def test_is_top_pick_nomination_false(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        self.assertFalse(IotdService().is_top_pick_nomination(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_is_top_pick_nomination_true_future_top_pick(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        self.assertTrue(IotdService().is_top_pick_nomination(image))

    def test_is_top_pick_nomination_false_still_in_queue(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)

        self.assertFalse(IotdService().is_top_pick_nomination(image))

    def test_get_iotds(self):
        iotd_image = Generators.image()
        Generators.image()
        Generators.premium_subscription(iotd_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=iotd_image)
        IotdGenerators.vote(image=iotd_image)
        IotdGenerators.iotd(image=iotd_image)

        iotds = IotdService().get_iotds()

        self.assertEqual(1, iotds.count())
        self.assertEqual(iotd_image, iotds.first().image)

    def test_get_iotds_future_date(self):
        iotd_image = Generators.image()
        Generators.image()
        Generators.premium_subscription(iotd_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=iotd_image)
        IotdGenerators.vote(image=iotd_image)
        IotdGenerators.iotd(image=iotd_image, date=date.today() + timedelta(days=1))

        iotds = IotdService().get_iotds()

        self.assertEqual(0, iotds.count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_top_picks(self):
        top_pick_image = Generators.image()
        Generators.image()
        Generators.premium_subscription(top_pick_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_pick_image.published = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS) - timedelta(hours=1)
        top_pick_image.save()

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEqual(1, top_picks.count())
        self.assertEqual(top_pick_image, top_picks.first().image)

    def test_get_top_picks_still_in_queue(self):
        top_pick_image = Generators.image()
        Generators.image()
        Generators.premium_subscription(top_pick_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_pick_image.published = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS) + timedelta(hours=1)
        top_pick_image.save()

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEqual(0, top_picks.count())

    def test_get_top_picks_is_past_iotd(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() - timedelta(days=1))

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEqual(0, top_picks.count())

    def test_get_top_picks_is_current_iotd(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEqual(0, top_picks.count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_top_picks_is_future_iotd(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() + timedelta(days=1))

        image.published = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS) - timedelta(hours=1)
        image.save()

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEqual(1, top_picks.count())
        self.assertEqual(image, top_picks.first().image)

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS + 1)
    )
    def test_get_top_picks_not_enough_votes_after_cutoff(self):
        top_pick_image = Generators.image()
        Generators.image()
        Generators.premium_subscription(top_pick_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_pick_image.published = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START + timedelta(hours=1)
        top_pick_image.save()

        IotdService().update_top_pick_archive()

        self.assertEqual(0, IotdService().get_top_picks().count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS + 1)
    )
    def test_get_top_picks_not_enough_votes_before_cutoff(self):
        top_pick_image = Generators.image()
        Generators.image()
        Generators.premium_subscription(top_pick_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_pick_image.published = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(hours=1)
        top_pick_image.save()

        IotdService().update_top_pick_archive()

        self.assertEqual(1, IotdService().get_top_picks().count())

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS + 1)
    )
    def test_get_top_pick_nominations_only_one_submission_after_cutoff(self):
        image = Generators.image()

        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)

        image.published = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(hours=1)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(0, nominations.count())

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS + 1)
    )
    def test_get_top_pick_nominations_only_one_submission_before_cutoff(self):
        image = Generators.image()

        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)

        image.published = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(hours=1)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(1, nominations.count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_get_top_pick_nominations(self):
        image = Generators.image()

        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)

        image.published = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(hours=1)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(1, nominations.count())
        self.assertEqual(image, nominations.first().image)

    def test_get_top_pick_nominations_too_soon(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(0, nominations.count())

    def test_get_top_pick_nominations_has_vote(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(0, nominations.count())

    def test_get_top_pick_nominations_has_no_submission(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(0, nominations.count())

    def test_get_submission_queue_spam(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)

        self.assertEqual(1, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.moderator_decision = 2
        image.save()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_published_too_long_ago(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.published = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(hours=1)
        image.save()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_other_type(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.subject_type = SubjectType.OTHER
        image.save()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_gear_type(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.subject_type = SubjectType.GEAR
        image.save()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_already_submitted_today(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        self.assertEqual(1, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_already_submitted_before_window(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS + 1)
        image.save()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_dismissed(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)

        IotdDismissedImage.objects.create(
            user=submitter,
            image=image
        )

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    @override_settings(IOTD_MAX_DISMISSALS=3)
    def test_get_submission_queue_dismissed_3_times(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")
        image = Generators.image(user=user)

        submitter1 = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        submitter3 = Generators.user(groups=['iotd_submitters'])
        submitter4 = Generators.user(groups=['iotd_submitters'])

        image.designated_iotd_submitters.add(submitter4)

        IotdDismissedImage.objects.create(user=submitter1, image=image)
        IotdDismissedImage.objects.create(user=submitter2, image=image)

        self.assertEqual(1, len(IotdService().get_submission_queue(submitter4)))

        IotdDismissedImage.objects.create(user=submitter3, image=image)

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter4)))

    def test_get_submission_queue_already_iotd(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=datetime.now().date() - timedelta(1))

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_future_iotd(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=datetime.now().date() + timedelta(1))

        self.assertEqual(1, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_sort_order(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")
        image1 = Generators.image(user=user, published=DateTimeService.now() - timedelta(hours=1))
        image2 = Generators.image(user=user, published=DateTimeService.now())

        submitter = Generators.user(groups=['iotd_submitters'])

        image1.designated_iotd_submitters.add(submitter)
        image2.designated_iotd_submitters.add(submitter)

        queue = IotdService().get_submission_queue(submitter)
        self.assertEqual(2, len(queue))
        self.assertEqual(image1, queue[1])
        self.assertEqual(image2, queue[0])

        queue = IotdService().get_submission_queue(submitter, 'oldest')
        self.assertEqual(2, len(queue))
        self.assertEqual(image1, queue[0])
        self.assertEqual(image2, queue[1])

        self.assertTrue(
            IotdStaffMemberSettings.objects
                .filter(user=submitter, queue_sort_order=IotdQueueSortOrder.OLDEST_FIRST)
                .exists()
        )

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_get_review_queue(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_get_review_queue_deleted(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        image.delete()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS + 1)
    )
    def test_get_review_queue_not_enough_submissions_after_cutoff(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        image.published = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START + timedelta(hours=1)

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_not_enough_submissions_before_cutoff(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        image.published = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(1)
        image.save()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_not_designated(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.remove(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_too_long_ago(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        submission = IotdSubmission.objects.create(
            submitter=submitter,
            image=image,
        )

        submission.date = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS + 1)
        submission.save()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_review_queue_submitted_two_days_ago(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer)

        submission = IotdSubmission.objects.create(
            submitter=submitter,
            image=image,
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image,
        )

        submission.date = datetime.now() - timedelta(days=2)
        submission.save()

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_current_iotd(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer1 = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer2)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer1,
            image=image
        )

        Iotd.objects.create(
            date=date.today(),
            judge=judge,
            image=image
        )

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer2)))

    def test_get_review_queue_past_iotd(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer1 = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer2)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer1,
            image=image
        )

        Iotd.objects.create(
            date=date.today() - timedelta(days=1),
            judge=judge,
            image=image
        )

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer2)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_review_queue_future_iotd(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer1 = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])
        reviewer3 = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer3)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer1,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer2,
            image=image
        )

        Iotd.objects.create(
            date=date.today() + timedelta(days=1),
            judge=judge,
            image=image
        )

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer3)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1)
    def test_get_review_queue_already_reviewed_today(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer,
            image=image
        )

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_already_reviewed_yesterday(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        vote = IotdVote.objects.create(
            reviewer=reviewer,
            image=image
        )

        vote.date = datetime.now() - timedelta(days=1)
        vote.save()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_dismissed(self):
        uploader = Generators.user()
        submitter1 = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        submitter3 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter1, submitter2, submitter3)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(submitter=submitter1, image=image)
        IotdSubmission.objects.create(submitter=submitter2, image=image)
        IotdSubmission.objects.create(submitter=submitter3, image=image)

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

        IotdDismissedImage.objects.create(user=reviewer, image=image)

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_MAX_DISMISSALS=3)
    def test_get_review_queue_dismissed_3_times_by_submitters(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")
        image = Generators.image(user=user)

        submitter1 = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        submitter3 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        image.designated_iotd_submitters.add(submitter1, submitter2, submitter3)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(submitter=submitter1, image=image)
        IotdSubmission.objects.create(submitter=submitter2, image=image)
        IotdSubmission.objects.create(submitter=submitter3, image=image)

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

        IotdDismissedImage.objects.create(user=submitter1, image=image)
        IotdDismissedImage.objects.create(user=submitter2, image=image)

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

        IotdDismissedImage.objects.create(user=submitter3, image=image)

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_sort_order(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")
        image1 = Generators.image(user=user, published=DateTimeService.now() - timedelta(hours=1))
        image2 = Generators.image(user=user, published=DateTimeService.now())

        submitter1 = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        submitter3 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        image1.designated_iotd_submitters.add(submitter1, submitter2, submitter3)
        image1.designated_iotd_reviewers.add(reviewer)

        image2.designated_iotd_submitters.add(submitter1, submitter2, submitter3)
        image2.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(submitter=submitter1, image=image1)
        IotdSubmission.objects.create(submitter=submitter2, image=image1)
        IotdSubmission.objects.create(submitter=submitter3, image=image1)

        IotdSubmission.objects.create(submitter=submitter1, image=image2)
        IotdSubmission.objects.create(submitter=submitter2, image=image2)
        IotdSubmission.objects.create(submitter=submitter3, image=image2)

        queue = IotdService().get_review_queue(reviewer)
        self.assertEqual(2, len(queue))
        self.assertEqual(image1, queue[1])
        self.assertEqual(image2, queue[0])

        queue = IotdService().get_review_queue(reviewer, 'oldest')
        self.assertEqual(2, len(queue))
        self.assertEqual(image1, queue[0])
        self.assertEqual(image2, queue[1])

        self.assertTrue(
            IotdStaffMemberSettings.objects
                .filter(user=reviewer, queue_sort_order=IotdQueueSortOrder.OLDEST_FIRST)
                .exists()
        )

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer, reviewer2)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer2,
            image=image
        )

        self.assertEqual(1, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_deleted(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer, reviewer2)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer2,
            image=image
        )

        image.delete()

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    @override_settings(IOTD_MAX_DISMISSALS=3)
    def test_get_judgement_queue_dismissed_3_times(self):
        uploader = Generators.user()
        submitter1 = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer1 = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter1, submitter2)
        image.designated_iotd_reviewers.add(reviewer1, reviewer2)

        IotdSubmission.objects.create(
            submitter=submitter1,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer1,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer2,
            image=image
        )

        self.assertEqual(1, len(IotdService().get_judgement_queue(judge)))

        IotdDismissedImage.objects.create(image=image, user=submitter1)
        IotdDismissedImage.objects.create(image=image, user=submitter2)

        self.assertEqual(1, len(IotdService().get_judgement_queue(judge)))

        IotdDismissedImage.objects.create(image=image, user=reviewer1)

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_too_long_ago(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer, reviewer2)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        vote = IotdVote.objects.create(
            reviewer=reviewer,
            image=image
        )

        vote2 = IotdVote.objects.create(
            reviewer=reviewer2,
            image=image
        )

        vote.date = datetime.now() - timedelta(days=settings.IOTD_JUDGEMENT_WINDOW_DAYS + 1)
        vote.save()

        vote2.date = datetime.now() - timedelta(days=settings.IOTD_JUDGEMENT_WINDOW_DAYS + 1)
        vote2.save()

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_future_iotd(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer, reviewer2)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer2,
            image=image
        )

        Iotd.objects.create(
            judge=judge,
            image=image,
            date=date.today() + timedelta(1)
        )

        self.assertEqual(1, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_current_iotd(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer, reviewer2)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer2,
            image=image
        )

        Iotd.objects.create(
            judge=judge,
            image=image,
            date=date.today()
        )

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_past_iotd(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer, reviewer2)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer2,
            image=image
        )

        Iotd.objects.create(
            judge=judge,
            image=image,
            date=date.today() - timedelta(1)
        )

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))


    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_JUDGEMENT_WINDOW_DAYS)
    )
    def test_get_judgement_not_enough_votes_after_cutoff(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer,
            image=image
        )

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_JUDGEMENT_WINDOW_DAYS + 1)
    )
    def test_get_judgement_not_enough_votes_before_cutoff(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])
        judge = Generators.user(groups=['iotd_judges'])

        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        IotdVote.objects.create(
            reviewer=reviewer,
            image=image
        )

        image.published = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(hours=1)
        image.save()

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))

    @patch('common.services.DateTimeService.now')
    def test_judge_cannot_select_now_reason_none_no_iotds(self, now):
        now.return_value = datetime.now()
        judge = Generators.user(groups=['iotd_judges'])
        self.assertIsNone(IotdService().judge_cannot_select_now_reason(judge))
        self.assertEqual(IotdService().get_next_available_selection_time_for_judge(judge), DateTimeService.now())

    @patch('common.services.DateTimeService.now')
    def test_judge_cannot_select_now_reason_none_no_scheduled_iotds(self, now):
        now.return_value = datetime.now()
        iotd = self._create_iotd(date=date.today() - timedelta(1))
        self.assertIsNone(IotdService().judge_cannot_select_now_reason(iotd.judge))
        self.assertEqual(IotdService().get_next_available_selection_time_for_judge(iotd.judge), DateTimeService.now())

    @override_settings(IOTD_JUDGEMENT_MAX_PER_DAY=1)
    @patch('common.services.DateTimeService.now')
    def test_judge_cannot_select_now_reason_already_selected_today(self, now):
        now.return_value = datetime.now()
        iotd = self._create_iotd(date=date.today())
        reason = IotdService().judge_cannot_select_now_reason(iotd.judge)
        self.assertIsNotNone(reason)
        self.assertTrue('you already selected 1 IOTD today' in reason)
        self.assertEqual(
            IotdService().get_next_available_selection_time_for_judge(iotd.judge),
            DateTimeService.next_midnight())

    @override_settings(IOTD_JUDGEMENT_MAX_PER_DAY=2, IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE=2)
    @patch('common.services.DateTimeService.now')
    def test_judge_cannot_select_now_reason_already_2_scheduled(self, now):
        now.return_value = datetime.now()
        iotd = self._create_iotd(date=date.today() + timedelta(1))
        self._create_iotd(judge=iotd.judge, date=date.today() + timedelta(2))
        reason = IotdService().judge_cannot_select_now_reason(iotd.judge)
        self.assertIsNotNone(reason)
        self.assertTrue('you already selected 2 scheduled IOTDs' in reason)
        self.assertEqual(
            IotdService().get_next_available_selection_time_for_judge(iotd.judge),
            DateTimeService.next_midnight(iotd.date))

    @override_settings(
        IOTD_JUDGEMENT_MAX_PER_DAY=2,
        IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE=3,
        IOTD_JUDGEMENT_MAX_FUTURE_DAYS=2
    )
    @patch('common.services.DateTimeService.now')
    def test_judge_cannot_select_now_reason_already_2_scheduled(self, now):
        now.return_value = datetime.now()
        iotd = self._create_iotd(date=date.today() + timedelta(1))
        self._create_iotd(judge=iotd.judge, date=date.today() + timedelta(2))
        reason = IotdService().judge_cannot_select_now_reason(iotd.judge)
        self.assertIsNotNone(reason)
        self.assertTrue('there are already 2 scheduled IOTDs' in reason)
        self.assertEqual(
            IotdService().get_next_available_selection_time_for_judge(iotd.judge),
            DateTimeService.next_midnight())

    def test_inactive_submitters_no_submissions(self):
        submitter = Generators.user(groups=['iotd_submitters'])
        self.assertTrue(submitter in IotdService().get_inactive_submitter_and_reviewers(3))

    def test_inactive_submitters_superuser(self):
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter.is_superuser = True
        submitter.save()

        self.assertFalse(submitter in IotdService().get_inactive_submitter_and_reviewers(3))

    def test_inactive_submitters_no_recent_submissions(self):
        uploader = Generators.user()
        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)

        submission = IotdGenerators.submission(submitter=submitter, image=image)
        submission.date = DateTimeService.now() - timedelta(days=5)
        submission.save()

        self.assertFalse(submitter in IotdService().get_inactive_submitter_and_reviewers(4))
        self.assertTrue(submitter in IotdService().get_inactive_submitter_and_reviewers(5))
        self.assertFalse(submitter in IotdService().get_inactive_submitter_and_reviewers(6))

    def test_inactive_submitters_recent_submissions(self):
        uploader = Generators.user()
        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)

        IotdGenerators.submission(submitter=submitter, image=image)

        self.assertFalse(submitter in IotdService().get_inactive_submitter_and_reviewers(3))

    def test_inactive_reviewers_no_votes(self):
        uploader = Generators.user()
        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        IotdGenerators.submission(submitter=submitter, image=image)

        self.assertTrue(reviewer in IotdService().get_inactive_submitter_and_reviewers(3))

    def test_inactive_reviewers_no_recent_votes(self):
        uploader = Generators.user()
        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        IotdGenerators.submission(submitter=submitter, image=image)
        vote = IotdGenerators.vote(reviewer=reviewer, image=image)
        vote.date = DateTimeService.now() - timedelta(days=5)
        vote.save()

        self.assertFalse(reviewer in IotdService().get_inactive_submitter_and_reviewers(4))
        self.assertTrue(reviewer in IotdService().get_inactive_submitter_and_reviewers(5))
        self.assertFalse(reviewer in IotdService().get_inactive_submitter_and_reviewers(6))

    def test_inactive_reviewers_recent_votes(self):
        uploader = Generators.user()
        Generators.premium_subscription(uploader, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])

        image = Generators.image(user=uploader)
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        IotdGenerators.submission(submitter=submitter, image=image)
        IotdGenerators.vote(reviewer=reviewer, image=image)

        self.assertFalse(reviewer in IotdService().get_inactive_submitter_and_reviewers(3))

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_unauthenticated(self, is_authenticated):
        is_authenticated.return_value = False

        image = Generators.image()
        user = Generators.user()

        self.assertEqual((False, 'UNAUTHENTICATED'), IotdService.may_submit_to_iotd_tp_process(user, image))

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_not_owner(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        user = Generators.user()

        self.assertEqual((False, 'NOT_OWNER'), IotdService.may_submit_to_iotd_tp_process(user, image))

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_is_free(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()

        self.assertEqual((False, 'IS_FREE'), IotdService.may_submit_to_iotd_tp_process(image.user, image))

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_not_published(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image(is_wip=True)
        Generators.premium_subscription(image.user, "AstroBin Ultimate 2020+")

        self.assertEqual((False, 'NOT_PUBLISHED'), IotdService.may_submit_to_iotd_tp_process(image.user, image))

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_already_submitted(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        Generators.premium_subscription(image.user, "AstroBin Ultimate 2020+")
        image.designated_iotd_submitters.add(Generators.user(groups=['iotd_staff', 'iotd_submitters']))
        image.designated_iotd_reviewers.add(Generators.user(groups=['iotd_staff', 'iotd_reviewers']))

        self.assertEqual((False, 'ALREADY_SUBMITTED'), IotdService.may_submit_to_iotd_tp_process(image.user, image))

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_already_bad_type(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image(subject_type=SubjectType.GEAR)
        Generators.premium_subscription(image.user, "AstroBin Ultimate 2020+")

        self.assertEqual((False, 'BAD_SUBJECT_TYPE'), IotdService.may_submit_to_iotd_tp_process(image.user, image))

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_excluded_from_competitions(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        Generators.premium_subscription(image.user, "AstroBin Ultimate 2020+")
        image.user.userprofile.exclude_from_competitions = True
        image.user.userprofile.save(keep_deleted=True)

        self.assertEqual(
            (False, 'EXCLUDED_FROM_COMPETITIONS'), IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_banned_from_competitions(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        Generators.premium_subscription(image.user, "AstroBin Ultimate 2020+")
        image.user.userprofile.banned_from_competitions = datetime.now()
        image.user.userprofile.save(keep_deleted=True)

        self.assertEqual(
            (False, 'BANNED_FROM_COMPETITIONS'), IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_too_late(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        Generators.premium_subscription(image.user, "AstroBin Ultimate 2020+")
        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS + 1)
        image.save(keep_deleted=True)

        self.assertEqual(
            (False, 'TOO_LATE'), IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_all_ok(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        Generators.premium_subscription(image.user, "AstroBin Ultimate 2020+")

        self.assertEqual(
            (True, None), IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('astrobin_apps_iotd.services.IotdService.may_submit_to_iotd_tp_process')
    def test_submit_to_iotd_tp_process_no_autosubmit(self, may_submit_to_iotd_tp_process):
        may_submit_to_iotd_tp_process.return_value = True, None

        submitter = Generators.user(groups=['iotd_staff', 'iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_staff', 'iotd_reviewers'])
        image = Generators.image()

        IotdService.submit_to_iotd_tp_process(image.user, image, False)

        self.assertTrue(image.designated_iotd_submitters.exists())
        self.assertTrue(submitter, image.designated_iotd_submitters.first())

        self.assertTrue(image.designated_iotd_reviewers.exists())
        self.assertTrue(reviewer, image.designated_iotd_reviewers.first())

        self.assertFalse(image.user.userprofile.auto_submit_to_iotd_tp_process)

    @patch('astrobin_apps_iotd.services.IotdService.may_submit_to_iotd_tp_process')
    def test_submit_to_iotd_tp_process_autosubmit(self, may_submit_to_iotd_tp_process):
        may_submit_to_iotd_tp_process.return_value = True, None

        submitter = Generators.user(groups=['iotd_staff', 'iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_staff', 'iotd_reviewers'])
        image = Generators.image()

        IotdService.submit_to_iotd_tp_process(image.user, image, True)

        self.assertTrue(image.designated_iotd_submitters.exists())
        self.assertTrue(submitter, image.designated_iotd_submitters.first())

        self.assertTrue(image.designated_iotd_reviewers.exists())
        self.assertTrue(reviewer, image.designated_iotd_reviewers.first())

        self.assertTrue(image.user.userprofile.auto_submit_to_iotd_tp_process)

    @patch('astrobin_apps_iotd.services.IotdService.may_submit_to_iotd_tp_process')
    def test_submit_to_iotd_tp_process_may_not(self, may_submit_to_iotd_tp_process):
        may_submit_to_iotd_tp_process.return_value = False, 'ALREADY_SUBMITTED'

        Generators.user(groups=['iotd_staff', 'iotd_submitters'])
        Generators.user(groups=['iotd_staff', 'iotd_reviewers'])
        image = Generators.image()

        IotdService.submit_to_iotd_tp_process(image.user, image, False)

        self.assertFalse(image.designated_iotd_submitters.exists())
        self.assertFalse(image.designated_iotd_reviewers.exists())
