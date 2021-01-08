from datetime import timedelta, date, datetime

from django.conf import settings
from django.test import TestCase

from astrobin.enums import SubjectType
from astrobin.tests.generators import Generators
from astrobin_apps_iotd.models import IotdSubmission
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.tests.iotd_generators import IotdGenerators


class IotdServiceTest(TestCase):
    def test_is_iotd_true(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        self.assertTrue(IotdService().is_iotd(image))

    def test_is_iotd_false(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        self.assertFalse(IotdService().is_iotd(image))

    def test_is_iotd_false_future(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        iotd = IotdGenerators.iotd(image=image, date=date.today() + timedelta(days=1))

        self.assertFalse(IotdService().is_iotd(image))

    def test_is_iotd_false_excluded(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        image.user.userprofile.exclude_from_competitions = True
        image.user.userprofile.save()

        self.assertFalse(IotdService().is_iotd(image))

    def test_is_top_pick_true(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        self.assertTrue(IotdService().is_top_pick(image))

    def test_is_top_pick_false(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        self.assertFalse(IotdService().is_top_pick(image))

    def test_is_top_picks_false_already_iotd(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        self.assertFalse(IotdService().is_top_pick(image))

    def test_is_top_picks_true_future_iotd(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() + timedelta(days=1))

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        self.assertTrue(IotdService().is_top_pick(image))

    def test_is_top_pick_false_excluded(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        image.user.userprofile.exclude_from_competitions = True
        image.user.userprofile.save()

        self.assertFalse(IotdService().is_top_pick(image))

    def test_is_top_pick_nomination_true(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        self.assertTrue(IotdService().is_top_pick_nomination(image))

    def test_is_top_pick_nomination_false(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        self.assertFalse(IotdService().is_top_pick_nomination(image))

    def test_is_top_pick_nomination_false_already_top_pick(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        self.assertFalse(IotdService().is_top_pick_nomination(image))

    def test_is_top_pick_nomination_true_future_top_pick(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        self.assertTrue(IotdService().is_top_pick_nomination(image))

    def test_is_top_pick_nomination_false_still_in_queue(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)

        self.assertFalse(IotdService().is_top_pick_nomination(image))

    def test_is_top_pick_nomination_false_excluded(self):
        image = Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')
        IotdGenerators.submission(image=image)

        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        image.user.userprofile.exclude_from_competitions = True
        image.user.userprofile.save()

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

    def test_get_top_picks(self):
        top_pick_image = Generators.image()
        Generators.image()
        Generators.premium_subscription(top_pick_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_pick_image.published = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS) - timedelta(hours=1)
        top_pick_image.save()

        top_picks = IotdService().get_top_picks()

        self.assertEquals(1, top_picks.count())
        self.assertEquals(top_pick_image, top_picks.first())

    def test_get_top_picks(self):
        top_pick_image = Generators.image()
        Generators.image()
        Generators.premium_subscription(top_pick_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_pick_image.published = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS) + timedelta(hours=1)
        top_pick_image.save()

        top_picks = IotdService().get_top_picks()

        self.assertEquals(0, top_picks.count())

    def test_get_top_picks_corrupted(self):
        top_pick_image = Generators.image(corrupted=True)
        Generators.image()
        Generators.premium_subscription(top_pick_image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_picks = IotdService().get_top_picks()

        self.assertEquals(0, top_picks.count())

    def test_get_top_picks_is_past_iotd(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() - timedelta(days=1))

        top_picks = IotdService().get_top_picks()

        self.assertEquals(0, top_picks.count())

    def test_get_top_picks_is_current_iotd(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        top_picks = IotdService().get_top_picks()

        self.assertEquals(0, top_picks.count())

    def test_get_top_picks_is_future_iotd(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() + timedelta(days=1))

        image.published = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS) - timedelta(hours=1)
        image.save()

        top_picks = IotdService().get_top_picks()

        self.assertEquals(1, top_picks.count())
        self.assertEquals(image, top_picks.first())

    def test_get_top_pick_nominations(self):
        image = Generators.image()

        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)

        image.published = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(hours=1)
        image.save()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEquals(1, nominations.count())
        self.assertEquals(image, nominations.first())

    def test_get_top_pick_nominations_too_soon(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)

        nominations = IotdService().get_top_pick_nominations()

        self.assertEquals(0, nominations.count())

    def test_get_top_pick_nominations_corrupted(self):
        image = Generators.image(corrupted=True)
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)

        nominations = IotdService().get_top_pick_nominations()

        self.assertEquals(0, nominations.count())

    def test_get_top_pick_nominations_has_vote(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        nominations = IotdService().get_top_pick_nominations()

        self.assertEquals(0, nominations.count())

    def test_get_top_pick_nominations_has_no_submission(self):
        image = Generators.image()
        Generators.image()
        Generators.premium_subscription(image.user, 'AstroBin Ultimate 2020+')

        nominations = IotdService().get_top_pick_nominations()

        self.assertEquals(0, nominations.count())

    def test_get_submission_queue_spam(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.moderator_decision = 2
        image.save()

        self.assertEquals(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_spam_published_too_long_ago(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.published = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(hours=1)
        image.save()

        self.assertEquals(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_spam_other_type(self):
        user = Generators.user()
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        submitter = Generators.user(groups=['iotd_submitters'])
        image = Generators.image(user=user)
        image.designated_iotd_submitters.add(submitter)
        image.subject_type = SubjectType.OTHER
        image.save()

        self.assertEquals(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_spam_gear_type(self):
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
