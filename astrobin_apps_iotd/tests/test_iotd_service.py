from datetime import timedelta, date, datetime

from django.conf import settings
from django.test import TestCase, override_settings

from astrobin.enums import SubjectType
from astrobin.tests.generators import Generators
from astrobin_apps_iotd.models import IotdSubmission, IotdVote, Iotd, IotdDismissedImage
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.tests.iotd_generators import IotdGenerators


class IotdServiceTest(TestCase):
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

    def test_is_top_pick_nomination_false_already_top_pick(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
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

        self.assertEquals(1, iotds.count())
        self.assertEquals(iotd_image, iotds.first().image)

    def test_get_iotds_future_date(self):
        iotd_image = Generators.image()
        Generators.image()
        Generators.premium_subscription(iotd_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=iotd_image)
        IotdGenerators.vote(image=iotd_image)
        IotdGenerators.iotd(image=iotd_image, date=date.today() + timedelta(days=1))

        iotds = IotdService().get_iotds()

        self.assertEquals(0, iotds.count())

    def test_get_iotds_corrupted(self):
        iotd_image = Generators.image(corrupted=True)
        Generators.image()
        Generators.premium_subscription(iotd_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=iotd_image)
        IotdGenerators.vote(image=iotd_image)
        IotdGenerators.iotd(image=iotd_image)

        iotds = IotdService().get_iotds()

        self.assertEquals(0, iotds.count())

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

        self.assertEquals(1, top_picks.count())
        self.assertEquals(top_pick_image, top_picks.first().image)

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

        self.assertEquals(0, top_picks.count())

    def test_get_top_picks_corrupted(self):
        top_pick_image = Generators.image(corrupted=True)
        Generators.image()
        Generators.premium_subscription(top_pick_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEquals(0, top_picks.count())

    def test_get_top_picks_is_past_iotd(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() - timedelta(days=1))

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEquals(0, top_picks.count())

    def test_get_top_picks_is_current_iotd(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEquals(0, top_picks.count())

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

        self.assertEquals(1, top_picks.count())
        self.assertEquals(image, top_picks.first().image)

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

        self.assertEquals(0, IotdService().get_top_picks().count())

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

        self.assertEquals(1, IotdService().get_top_picks().count())

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

        self.assertEquals(0, nominations.count())

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

        self.assertEquals(1, nominations.count())

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

        self.assertEquals(1, nominations.count())
        self.assertEquals(image, nominations.first().image)

    def test_get_top_pick_nominations_too_soon(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEquals(0, nominations.count())

    def test_get_top_pick_nominations_corrupted(self):
        image = Generators.image(corrupted=True)
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEquals(0, nominations.count())

    def test_get_top_pick_nominations_has_vote(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEquals(0, nominations.count())

    def test_get_top_pick_nominations_has_no_submission(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEquals(0, nominations.count())

    def test_get_submission_queue_spam(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)

        self.assertEquals(1, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.moderator_decision = 2
        image.save()

        self.assertEquals(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_published_too_long_ago(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.published = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(hours=1)
        image.save()

        self.assertEquals(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_other_type(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.subject_type = SubjectType.OTHER
        image.save()

        self.assertEquals(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_gear_type(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.subject_type = SubjectType.GEAR
        image.save()

        self.assertEquals(0, len(IotdService().get_submission_queue(submitter)))

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

        self.assertEquals(1, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_already_submitted_yesterday(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        image.published = datetime.now() - timedelta(hours=24)
        image.save()

        self.assertEquals(0, len(IotdService().get_submission_queue(submitter)))

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

        self.assertEquals(0, len(IotdService().get_submission_queue(submitter)))

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

        self.assertEquals(1, len(IotdService().get_review_queue(reviewer)))

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

        self.assertEquals(0, len(IotdService().get_review_queue(reviewer)))

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

        self.assertEquals(0, len(IotdService().get_review_queue(reviewer)))

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

        self.assertEquals(0, len(IotdService().get_review_queue(reviewer)))

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

        self.assertEquals(0, len(IotdService().get_review_queue(reviewer)))

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

        self.assertEquals(1, len(IotdService().get_review_queue(reviewer)))

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

        self.assertEquals(0, len(IotdService().get_review_queue(reviewer2)))

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

        self.assertEquals(0, len(IotdService().get_review_queue(reviewer2)))

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

        self.assertEquals(1, len(IotdService().get_review_queue(reviewer3)))

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

        self.assertEquals(1, len(IotdService().get_review_queue(reviewer)))

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

        self.assertEquals(0, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_dismissed(self):
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

        IotdDismissedImage.objects.create(
            user=reviewer,
            image=image
        )

        self.assertEquals(0, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])

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

        self.assertEquals(1, len(IotdService().get_judgement_queue()))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_too_long_ago(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=['iotd_submitters'])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=['iotd_reviewers'])
        reviewer2 = Generators.user(groups=['iotd_reviewers'])

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

        self.assertEquals(0, len(IotdService().get_judgement_queue()))

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

        self.assertEquals(1, len(IotdService().get_judgement_queue()))

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

        self.assertEquals(0, len(IotdService().get_judgement_queue()))

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

        self.assertEquals(0, len(IotdService().get_judgement_queue()))


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

        self.assertEquals(0, len(IotdService().get_judgement_queue()))

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

        self.assertEquals(0, len(IotdService().get_judgement_queue()))
