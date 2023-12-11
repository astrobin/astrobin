import time
from datetime import date, datetime, timedelta

import mock
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from mock import PropertyMock, patch

from astrobin.enums import SubjectType
from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Image
from astrobin.tests.generators import Generators
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from astrobin_apps_iotd.models import (
    Iotd, IotdDismissedImage, IotdQueueSortOrder, IotdStaffMemberSettings, IotdSubmission, IotdVote,
)
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.tasks import update_judgement_queues, update_review_queues, update_submission_queues
from astrobin_apps_iotd.tests.iotd_generators import IotdGenerators
from astrobin_apps_iotd.types.may_not_submit_to_iotd_tp_reason import MayNotSubmitToIotdTpReason
from astrobin_apps_premium.services.premium_service import SubscriptionName
from common.constants import GroupName
from common.services import DateTimeService


class IotdServiceTest(TestCase):
    def _create_iotd(self, **kwargs):
        judge = kwargs.pop('judge', Generators.user(groups=[GroupName.IOTD_JUDGES]))
        when = kwargs.pop('date', date.today())

        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        return IotdGenerators.iotd(judge=judge, image=image, date=when)

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2, IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_is_iotd_true(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        self.assertTrue(IotdService().is_iotd(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_is_iotd_false(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        self.assertFalse(IotdService().is_iotd(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_is_iotd_false_future(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() + timedelta(days=1))

        self.assertFalse(IotdService().is_iotd(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_is_iotd_false_excluded(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        image.user.userprofile.exclude_from_competitions = True
        image.user.userprofile.save()

        self.assertFalse(IotdService().is_iotd(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_is_top_pick_false_only_one_vote_after_cutoff(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
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
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        image.submitted_for_iotd_tp_consideration = \
            datetime.now() - \
            timedelta(
                settings.IOTD_SUBMISSION_WINDOW_DAYS +
                settings.IOTD_REVIEW_WINDOW_DAYS +
                settings.IOTD_JUDGEMENT_WINDOW_DAYS
            ) - \
            timedelta(1)
        image.save()

        IotdService().update_top_pick_archive()

        self.assertTrue(IotdService().is_top_pick(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_is_top_pick_true(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        previously_updated = image.updated
        time.sleep(.1)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.vote(image=image)

        image.submitted_for_iotd_tp_consideration = \
            datetime.now() - \
            timedelta(
                settings.IOTD_SUBMISSION_WINDOW_DAYS +
                settings.IOTD_REVIEW_WINDOW_DAYS +
                settings.IOTD_JUDGEMENT_WINDOW_DAYS
            )
        image.save()

        IotdService().update_top_pick_archive()
        image.refresh_from_db()

        self.assertTrue(IotdService().is_top_pick(image))
        self.assertGreater(image.updated, previously_updated)

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS + 1)
    )
    def test_is_top_pick_false(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)

        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_archive()

        self.assertFalse(IotdService().is_top_pick(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_is_top_picks_false_already_iotd(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_archive()

        self.assertFalse(IotdService().is_top_pick(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_is_top_picks_true_future_iotd(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() + timedelta(days=1))

        image.submitted_for_iotd_tp_consideration = \
            datetime.now() - \
            timedelta(
                settings.IOTD_SUBMISSION_WINDOW_DAYS +
                settings.IOTD_REVIEW_WINDOW_DAYS +
                settings.IOTD_JUDGEMENT_WINDOW_DAYS
            )
        image.save()

        IotdService().update_top_pick_archive()

        self.assertTrue(IotdService().is_top_pick(image))

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS - 1)
    )
    def test_is_top_pick_nomination_false_only_one_submission_after_cutoff(self):
        image = Generators.image(submitted_for_iotd_tp_consideration=datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)

        image.submitted_for_iotd_tp_consideration = \
            datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        self.assertFalse(IotdService().is_top_pick_nomination(image))

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS - 1)
    )
    def test_is_top_pick_nomination_false_enough_submissions_but_could_still_become_top_pick(self):
        image = Generators.image(submitted_for_iotd_tp_consideration=datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)

        image.submitted_for_iotd_tp_consideration = \
            datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        self.assertFalse(IotdService().is_top_pick_nomination(image))

    @override_settings(
        IOTD_SUBMISSION_MIN_PROMOTIONS=2,
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(
            settings.IOTD_SUBMISSION_WINDOW_DAYS + settings.IOTD_REVIEW_WINDOW_DAYS + 1
        )
    )
    def test_is_top_pick_nomination_true_only_one_submission_before_cutoff(self):
        image = Generators.image(submitted_for_iotd_tp_consideration=datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)

        image.submitted_for_iotd_tp_consideration = \
            settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(minutes=1)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        self.assertTrue(IotdService().is_top_pick_nomination(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_is_top_pick_nomination_true(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        previously_updated = image.updated
        time.sleep(.1)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)

        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(
            days=settings.IOTD_SUBMISSION_WINDOW_DAYS + settings.IOTD_REVIEW_WINDOW_DAYS
        )
        image.save()

        IotdService().update_top_pick_nomination_archive()
        image.refresh_from_db()

        self.assertTrue(IotdService().is_top_pick_nomination(image))
        self.assertGreater(image.updated, previously_updated)

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS - 1)
    )
    def test_is_top_pick_nomination_false(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        self.assertFalse(IotdService().is_top_pick_nomination(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_is_top_pick_nomination_true_future_top_pick(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)

        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(
            days=settings.IOTD_SUBMISSION_WINDOW_DAYS + settings.IOTD_REVIEW_WINDOW_DAYS
        )
        image.save()

        IotdService().update_top_pick_nomination_archive()

        self.assertTrue(IotdService().is_top_pick_nomination(image))

    def test_is_top_pick_nomination_false_still_in_queue(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        IotdGenerators.submission(image=image)

        self.assertFalse(IotdService().is_top_pick_nomination(image))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_iotds(self):
        iotd_image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(iotd_image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=iotd_image)
        IotdGenerators.vote(image=iotd_image)
        IotdGenerators.iotd(image=iotd_image)

        iotds = IotdService().get_iotds()

        self.assertEqual(1, iotds.count())
        self.assertEqual(iotd_image, iotds.first().image)

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_iotds_future_date(self):
        iotd_image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(iotd_image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=iotd_image)
        IotdGenerators.vote(image=iotd_image)
        IotdGenerators.iotd(image=iotd_image, date=date.today() + timedelta(days=1))

        iotds = IotdService().get_iotds()

        self.assertEqual(0, iotds.count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_top_picks(self):
        top_pick_image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(top_pick_image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_pick_image.submitted_for_iotd_tp_consideration = \
            datetime.now() - \
            timedelta(
                settings.IOTD_SUBMISSION_WINDOW_DAYS +
                settings.IOTD_REVIEW_WINDOW_DAYS +
                settings.IOTD_JUDGEMENT_WINDOW_DAYS
            ) - \
            timedelta(hours=1)
        top_pick_image.save()

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEqual(1, top_picks.count())
        self.assertEqual(top_pick_image, top_picks.first().image)

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_top_picks_still_in_queue(self):
        top_pick_image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(top_pick_image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_pick_image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS) + timedelta(hours=1)
        top_pick_image.save()

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEqual(0, top_picks.count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_top_picks_is_past_iotd(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() - timedelta(days=1))

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEqual(0, top_picks.count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_top_picks_is_current_iotd(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        IotdService().update_top_pick_archive()

        top_picks = IotdService().get_top_picks()

        self.assertEqual(0, top_picks.count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_top_picks_is_future_iotd(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=date.today() + timedelta(days=1))

        image.submitted_for_iotd_tp_consideration = \
            datetime.now() - \
            timedelta(
                settings.IOTD_SUBMISSION_WINDOW_DAYS +
                settings.IOTD_REVIEW_WINDOW_DAYS +
                settings.IOTD_JUDGEMENT_WINDOW_DAYS
            ) - \
            timedelta(hours=1)
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
        top_pick_image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(top_pick_image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_pick_image.submitted_for_iotd_tp_consideration = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START + timedelta(hours=1)
        top_pick_image.save()

        IotdService().update_top_pick_archive()

        self.assertEqual(0, IotdService().get_top_picks().count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS + 1)
    )
    def test_get_top_picks_not_enough_votes_before_cutoff(self):
        top_pick_image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(top_pick_image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.submission(image=top_pick_image)
        IotdGenerators.vote(image=top_pick_image)

        top_pick_image.submitted_for_iotd_tp_consideration = \
            datetime.now() - \
            timedelta(
                settings.IOTD_SUBMISSION_WINDOW_DAYS +
                settings.IOTD_REVIEW_WINDOW_DAYS +
                settings.IOTD_JUDGEMENT_WINDOW_DAYS
            ) - \
            timedelta(hours=1)
        top_pick_image.save()

        IotdService().update_top_pick_archive()

        self.assertEqual(1, IotdService().get_top_picks().count())

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS + 1)
    )
    def test_get_top_pick_nominations_only_one_submission_after_cutoff(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())

        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=image)

        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(hours=1)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(0, nominations.count())

    @override_settings(
        IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START=datetime.now() - timedelta(
            settings.IOTD_SUBMISSION_WINDOW_DAYS + settings.IOTD_REVIEW_WINDOW_DAYS + 1
        )
    )
    def test_get_top_pick_nominations_only_one_submission_before_cutoff(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())

        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=image)

        image.submitted_for_iotd_tp_consideration = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(hours=1)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(1, nominations.count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_get_top_pick_nominations(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())

        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=image)
        IotdGenerators.submission(image=image)

        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(
            settings.IOTD_SUBMISSION_WINDOW_DAYS + settings.IOTD_REVIEW_WINDOW_DAYS
        ) - timedelta(hours=1)
        image.save()

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(1, nominations.count())
        self.assertEqual(image, nominations.first().image)

    def test_get_top_pick_nominations_too_soon(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=image)

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(0, nominations.count())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_top_pick_nominations_has_vote(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(0, nominations.count())

    def test_get_top_pick_nominations_has_no_submission(self):
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        IotdService().update_top_pick_nomination_archive()

        nominations = IotdService().get_top_pick_nominations()

        self.assertEqual(0, nominations.count())

    def test_get_submission_queue_spam(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)

        update_submission_queues()

        self.assertEqual(1, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_own_image(self):
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=submitter, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)

        update_submission_queues()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_own_image_as_collaborator(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.collaborators.add(submitter)
        image.designated_iotd_submitters.add(submitter)

        update_submission_queues()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.moderator_decision = ModeratorDecision.REJECTED
        image.save()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_published_too_long_ago(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(hours=1)
        image.save()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_other_type(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.subject_type = SubjectType.OTHER
        image.save()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_gear_type(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.subject_type = SubjectType.GEAR
        image.save()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_already_submitted_today(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        update_submission_queues()

        self.assertEqual(1, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_already_submitted_before_window(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS + 1)
        image.save()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_dismissed(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)

        IotdDismissedImage.objects.create(
            user=submitter,
            image=image
        )

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    @override_settings(IOTD_MAX_DISMISSALS=3)
    def test_get_submission_queue_dismissed_3_times(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())

        submitter1 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter3 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter4 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])

        image.designated_iotd_submitters.add(submitter4)

        IotdDismissedImage.objects.create(user=submitter1, image=image)
        IotdDismissedImage.objects.create(user=submitter2, image=image)

        update_submission_queues()

        self.assertEqual(1, len(IotdService().get_submission_queue(submitter4)))

        IotdDismissedImage.objects.create(user=submitter3, image=image)

        update_submission_queues()

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter4)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_submission_queue_already_iotd(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=datetime.now().date() - timedelta(1))

        self.assertEqual(0, len(IotdService().get_submission_queue(submitter)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_submission_queue_future_iotd(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image, date=datetime.now().date() + timedelta(1))

        update_submission_queues()

        self.assertEqual(1, len(IotdService().get_submission_queue(submitter)))

    def test_get_submission_queue_sort_order(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        image1 = Generators.image(user=user, submitted_for_iotd_tp_consideration=DateTimeService.now() - timedelta(hours=1))
        image2 = Generators.image(user=user, submitted_for_iotd_tp_consideration=DateTimeService.now())

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])

        image1.designated_iotd_submitters.add(submitter)
        image2.designated_iotd_submitters.add(submitter)

        update_submission_queues()

        queue = IotdService().get_submission_queue(submitter)
        self.assertEqual(2, len(queue))
        self.assertEqual(image1, queue[1])
        self.assertEqual(image2, queue[0])

        update_submission_queues()

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
    def test_get_review_queue_own_image(self):
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        image = Generators.image(user=reviewer, submitted_for_iotd_tp_consideration=datetime.now())
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

        update_review_queues()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_get_review_queue_own_image_as_collaborator(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer)
        image.collaborators.add(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        IotdSubmission.objects.create(
            submitter=submitter2,
            image=image
        )

        update_review_queues()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_get_review_queue(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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

        update_review_queues()

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    def test_get_review_queue_deleted(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        image.submitted_for_iotd_tp_consideration = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START + timedelta(hours=1)

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1)
    def test_get_review_queue_not_enough_submissions_before_cutoff(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        submission = IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        submission.date = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS + 1)
        submission.save()

        image.submitted_for_iotd_tp_consideration = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(1)
        image.save()

        update_review_queues()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

        image.submitted_for_iotd_tp_consideration = datetime.now()
        image.save()

        submission.date = datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS - 1)
        submission.save()

        image.submitted_for_iotd_tp_consideration = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(1)
        image.save()

        update_review_queues()

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_not_designated(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.remove(reviewer)

        IotdSubmission.objects.create(
            submitter=submitter,
            image=image
        )

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_too_long_ago(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        submission = IotdSubmission.objects.create(
            submitter=submitter,
            image=image,
        )

        submission.date = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS + 1)
        submission.save()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    @override_settings(
        IOTD_SUBMISSION_WINDOW_DAYS=1,
        IOTD_SUBMISSION_MIN_PROMOTIONS=2,
        IOTD_REVIEW_QUEUE_WINDOW=1,
        IOTD_REVIEW_WINDOW_DAYS=2,
    )
    def test_get_review_queue_submitted_outside_of_window(self):
        uploader = Generators.user()
        submitter1 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter1, submitter2)
        image.designated_iotd_reviewers.add(reviewer)

        submission1 = IotdGenerators.submission(submitter=submitter1, image=image)
        IotdSubmission.objects.filter(pk=submission1.pk).update(date=datetime.now() - timedelta(3))

        submission2 = IotdGenerators.submission(submitter=submitter2, image=image)
        IotdSubmission.objects.filter(pk=submission2.pk).update(date=datetime.now() - timedelta(3))

        update_review_queues()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

        IotdSubmission.objects.filter(pk=submission2.pk).update(date=datetime.now() - timedelta(1))

        update_review_queues()

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_review_queue_current_iotd(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer1 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_review_queue_past_iotd(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer1 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer1 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer3 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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

        update_review_queues()

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer3)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1)
    def test_get_review_queue_already_reviewed_today(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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

        update_review_queues()

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_get_review_queue_already_reviewed_yesterday(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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
        submitter1 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter3 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter1, submitter2, submitter3)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(submitter=submitter1, image=image)
        IotdSubmission.objects.create(submitter=submitter2, image=image)
        IotdSubmission.objects.create(submitter=submitter3, image=image)

        update_review_queues()

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

        IotdDismissedImage.objects.create(user=reviewer, image=image)

        update_review_queues()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    @override_settings(IOTD_MAX_DISMISSALS=3)
    def test_get_review_queue_dismissed_3_times_by_submitters(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=datetime.now())

        submitter1 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter3 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        image.designated_iotd_submitters.add(submitter1, submitter2, submitter3)
        image.designated_iotd_reviewers.add(reviewer)

        IotdSubmission.objects.create(submitter=submitter1, image=image)
        IotdSubmission.objects.create(submitter=submitter2, image=image)
        IotdSubmission.objects.create(submitter=submitter3, image=image)

        update_review_queues()

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

        IotdDismissedImage.objects.create(user=submitter1, image=image)
        IotdDismissedImage.objects.create(user=submitter2, image=image)

        update_review_queues()

        self.assertEqual(1, len(IotdService().get_review_queue(reviewer)))

        IotdDismissedImage.objects.create(user=submitter3, image=image)

        update_review_queues()

        self.assertEqual(0, len(IotdService().get_review_queue(reviewer)))

    def test_get_review_queue_sort_order(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        image1 = Generators.image(user=user, submitted_for_iotd_tp_consideration=DateTimeService.now() - timedelta(hours=1))
        image2 = Generators.image(user=user, submitted_for_iotd_tp_consideration=DateTimeService.now())

        submitter1 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter3 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

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

        update_review_queues()

        queue = IotdService().get_review_queue(reviewer)
        self.assertEqual(2, len(queue))
        self.assertEqual(image1, queue[1])
        self.assertEqual(image2, queue[0])

        update_review_queues()

        queue = IotdService().get_review_queue(reviewer, 'oldest')
        self.assertEqual(2, len(queue))
        self.assertEqual(image1, queue[0])
        self.assertEqual(image2, queue[1])

        self.assertTrue(
            IotdStaffMemberSettings.objects
                .filter(user=reviewer, queue_sort_order=IotdQueueSortOrder.OLDEST_FIRST)
                .exists()
        )

    def test_get_review_queue_last_submission_timestamp(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=DateTimeService.now() - timedelta(days=1))

        submitter1 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter3 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter4 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        image.designated_iotd_submitters.add(submitter1, submitter2, submitter3)
        image.designated_iotd_reviewers.add(reviewer)

        submission1 = IotdSubmission.objects.create(submitter=submitter1, image=image)
        submission2 = IotdSubmission.objects.create(submitter=submitter2, image=image)
        submission3 = IotdSubmission.objects.create(submitter=submitter3, image=image)
        submission4 = IotdSubmission.objects.create(submitter=submitter4, image=image)

        submission1.date = DateTimeService.now() - timedelta(hours=3)
        submission1.save()

        submission2.date = DateTimeService.now() - timedelta(hours=2)
        submission2.save()

        submission3.date = DateTimeService.now() - timedelta(hours=1)
        submission3.save()

        submission4.date = DateTimeService.now() - timedelta(minutes=1)
        submission4.save()

        update_review_queues()

        queue = IotdService().get_review_queue(reviewer)
        self.assertEqual(1, len(queue))
        self.assertEqual(image, queue[0])
        self.assertEqual(submission3.date, queue[0].last_submission_timestamp)

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_own_image(self):
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        image = Generators.image(user=judge, submitted_for_iotd_tp_consideration=datetime.now())
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

        update_judgement_queues()

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_own_image_as_collaborator(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter, submitter2)
        image.designated_iotd_reviewers.add(reviewer, reviewer2)
        image.collaborators.add(judge)

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

        update_judgement_queues()

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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

        update_judgement_queues()

        self.assertEqual(1, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_deleted(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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
        submitter1 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer1 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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

        update_judgement_queues()

        self.assertEqual(1, len(IotdService().get_judgement_queue(judge)))

        IotdDismissedImage.objects.create(image=image, user=submitter1)
        IotdDismissedImage.objects.create(image=image, user=submitter2)

        self.assertEqual(1, len(IotdService().get_judgement_queue(judge)))

        IotdDismissedImage.objects.create(image=image, user=reviewer1)

        update_judgement_queues()

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_too_long_ago(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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

        update_judgement_queues()

        self.assertEqual(1, len(IotdService().get_judgement_queue(judge)))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=2)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=2)
    def test_get_judgement_queue_current_iotd(self):
        uploader = Generators.user()
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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
        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
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

        image.submitted_for_iotd_tp_consideration = settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START - timedelta(hours=1)
        image.save()

        self.assertEqual(0, len(IotdService().get_judgement_queue(judge)))

    def test_get_judgement_queue_last_submission_timestamp(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=DateTimeService.now() - timedelta(days=1))

        submitter1 = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter2 = Generators.user(groups=['iotd_submitters'])
        submitter3 = Generators.user(groups=['iotd_submitters'])
        
        reviewer1 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer2 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer3 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer4 = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])

        image.designated_iotd_submitters.add(submitter1, submitter2, submitter3)
        image.designated_iotd_reviewers.add(reviewer1, reviewer2, reviewer3)

        submission1 = IotdSubmission.objects.create(submitter=submitter1, image=image)
        submission2 = IotdSubmission.objects.create(submitter=submitter2, image=image)
        submission3 = IotdSubmission.objects.create(submitter=submitter3, image=image)

        submission1.date = DateTimeService.now() - timedelta(hours=4)
        submission1.save()

        submission2.date = DateTimeService.now() - timedelta(hours=4)
        submission2.save()

        submission3.date = DateTimeService.now() - timedelta(hours=4)
        submission3.save()

        vote1 = IotdVote.objects.create(reviewer=reviewer1, image=image)
        vote2 = IotdVote.objects.create(reviewer=reviewer2, image=image)
        vote3 = IotdVote.objects.create(reviewer=reviewer3, image=image)
        vote4 = IotdVote.objects.create(reviewer=reviewer4, image=image)

        vote1.date = DateTimeService.now() - timedelta(hours=3)
        vote1.save()

        vote2.date = DateTimeService.now() - timedelta(hours=2)
        vote2.save()

        vote3.date = DateTimeService.now() - timedelta(hours=1)
        vote3.save()

        vote4.date = DateTimeService.now() - timedelta(minutes=1)
        vote4.save()

        update_judgement_queues()

        queue = IotdService().get_judgement_queue(judge)

        self.assertEqual(1, len(queue))
        self.assertEqual(image, queue[0])
        self.assertEqual(vote3.date, queue[0].last_vote_timestamp)
        
    @patch('common.services.DateTimeService.now')
    def test_judge_cannot_select_now_reason_none_no_iotds(self, now):
        now.return_value = datetime.now()
        judge = Generators.user(groups=[GroupName.IOTD_JUDGES])
        self.assertIsNone(IotdService().judge_cannot_select_now_reason(judge))
        self.assertEqual(IotdService().get_next_available_selection_time_for_judge(judge), DateTimeService.now())

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    @patch('common.services.DateTimeService.now')
    def test_judge_cannot_select_now_reason_none_no_scheduled_iotds(self, now):
        now.return_value = datetime.now()

        iotd = self._create_iotd(date=date.today() - timedelta(1))
        Iotd.objects.filter(pk=iotd.pk).update(created=datetime.now() - timedelta(1))

        self.assertIsNone(IotdService().judge_cannot_select_now_reason(iotd.judge))
        self.assertEqual(IotdService().get_next_available_selection_time_for_judge(iotd.judge), DateTimeService.now())

    @override_settings(IOTD_JUDGEMENT_MAX_PER_DAY=1, IOTD_SUBMISSION_MIN_PROMOTIONS = 1, IOTD_REVIEW_MIN_PROMOTIONS = 1)
    @patch('common.services.DateTimeService.now')
    def test_judge_cannot_select_now_reason_already_selected_today(self, now):
        now.return_value = datetime.now()
        iotd = self._create_iotd(date=date.today())
        reason = IotdService().judge_cannot_select_now_reason(iotd.judge)
        self.assertIsNotNone(reason)
        self.assertTrue('you already selected 1 IOTD(s) today' in reason)
        self.assertEqual(
            IotdService().get_next_available_selection_time_for_judge(iotd.judge),
            DateTimeService.next_midnight())

    @override_settings(
        IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1, IOTD_JUDGEMENT_MAX_PER_DAY=2,
        IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE=2
    )
    @patch('common.services.DateTimeService.now')
    def test_judge_cannot_select_now_reason_already_max_scheduled_by_judge(self, now):
        now.return_value = datetime.now()
        iotd1 = self._create_iotd(date=date.today() + timedelta(1))
        iotd2 = self._create_iotd(judge=iotd1.judge, date=date.today() + timedelta(2))

        Iotd.objects.filter(pk=iotd1.pk).update(created=datetime.now() - timedelta(2))
        Iotd.objects.filter(pk=iotd2.pk).update(created=datetime.now() - timedelta(3))

        reason = IotdService().judge_cannot_select_now_reason(iotd1.judge)
        self.assertIsNotNone(reason)
        self.assertTrue('you already selected 2 scheduled IOTD(s)' in reason)
        self.assertEqual(
            IotdService().get_next_available_selection_time_for_judge(iotd2.judge),
            DateTimeService.next_midnight(iotd2.date))

    @override_settings(
        IOTD_JUDGEMENT_MAX_PER_DAY=2,
        IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE=3,
        IOTD_JUDGEMENT_MAX_FUTURE_DAYS=2,
        IOTD_SUBMISSION_MIN_PROMOTIONS=1,
        IOTD_REVIEW_MIN_PROMOTIONS=1
    )
    @patch('common.services.DateTimeService.now')
    def test_judge_cannot_select_now_reason_already_max_scheduled(self, now):
        now.return_value = datetime.now()
        iotd1 = self._create_iotd(date=date.today() + timedelta(1))
        iotd2 = self._create_iotd(judge=iotd1.judge, date=date.today() + timedelta(2))

        Iotd.objects.filter(pk=iotd1.pk).update(created=datetime.now() - timedelta(2))
        Iotd.objects.filter(pk=iotd2.pk).update(created=datetime.now() - timedelta(3))

        reason = IotdService().judge_cannot_select_now_reason(iotd1.judge)
        self.assertIsNotNone(reason)
        self.assertTrue('there are already 2 scheduled IOTD(s)' in reason)
        self.assertEqual(
            IotdService().get_next_available_selection_time_for_judge(iotd1.judge),
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
        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=['iotd_submitters'])

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)

        submission = IotdGenerators.submission(submitter=submitter, image=image)
        submission.date = DateTimeService.now() - timedelta(days=5)
        submission.save()

        self.assertFalse(submitter in IotdService().get_inactive_submitter_and_reviewers(4))
        self.assertTrue(submitter in IotdService().get_inactive_submitter_and_reviewers(5))
        self.assertFalse(submitter in IotdService().get_inactive_submitter_and_reviewers(6))

    def test_inactive_submitters_recent_submissions(self):
        uploader = Generators.user()
        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=['iotd_submitters'])

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)

        IotdGenerators.submission(submitter=submitter, image=image)

        self.assertFalse(submitter in IotdService().get_inactive_submitter_and_reviewers(3))

    def test_inactive_reviewers_no_votes(self):
        uploader = Generators.user()
        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        IotdGenerators.submission(submitter=submitter, image=image)

        self.assertTrue(reviewer in IotdService().get_inactive_submitter_and_reviewers(3))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_inactive_reviewers_no_recent_votes(self):
        uploader = Generators.user()
        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        IotdGenerators.submission(submitter=submitter, image=image)
        vote = IotdGenerators.vote(reviewer=reviewer, image=image)
        vote.date = DateTimeService.now() - timedelta(days=5)
        vote.save()

        self.assertFalse(reviewer in IotdService().get_inactive_submitter_and_reviewers(4))
        self.assertTrue(reviewer in IotdService().get_inactive_submitter_and_reviewers(5))
        self.assertFalse(reviewer in IotdService().get_inactive_submitter_and_reviewers(6))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1, IOTD_REVIEW_MIN_PROMOTIONS=1)
    def test_inactive_reviewers_recent_votes(self):
        uploader = Generators.user()
        Generators.premium_subscription(uploader, SubscriptionName.ULTIMATE_2020)

        submitter = Generators.user(groups=['iotd_submitters'])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])

        image = Generators.image(user=uploader, submitted_for_iotd_tp_consideration=datetime.now())
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_reviewers.add(reviewer)

        IotdGenerators.submission(submitter=submitter, image=image)
        IotdGenerators.vote(reviewer=reviewer, image=image)

        self.assertFalse(reviewer in IotdService().get_inactive_submitter_and_reviewers(3))

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_unauthenticated(self, is_authenticated):
        is_authenticated.return_value = False

        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        user = Generators.user()

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.NOT_AUTHENTICATED),
            IotdService.may_submit_to_iotd_tp_process(user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_not_owner(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        user = Generators.user()

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.NOT_OWNER), IotdService.may_submit_to_iotd_tp_process(user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_is_free(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.IS_FREE), IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_not_published(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image(is_wip=True)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.NOT_PUBLISHED),
            IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_already_submitted(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.designated_iotd_submitters.add(Generators.user(groups=[GroupName.IOTD_STAFF, 'iotd_submitters']))
        image.designated_iotd_reviewers.add(Generators.user(groups=[GroupName.IOTD_STAFF, GroupName.IOTD_REVIEWERS]))

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.ALREADY_SUBMITTED),
            IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_already_bad_type(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image(subject_type=SubjectType.GEAR)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.BAD_SUBJECT_TYPE),
            IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_excluded_from_competitions(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.exclude_from_competitions = True
        image.user.userprofile.save(keep_deleted=True)

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.EXCLUDED_FROM_COMPETITIONS),
            IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_banned_from_competitions(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.banned_from_competitions = datetime.now()
        image.user.userprofile.save(keep_deleted=True)

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.BANNED_FROM_COMPETITIONS),
            IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_too_late(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.published = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_FOR_CONSIDERATION_WINDOW_DAYS + 1)
        image.save(keep_deleted=True)

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.TOO_LATE), IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_no_telescope_no_camera(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.NO_TELESCOPE_OR_CAMERA),
            IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_no_camera(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.NO_TELESCOPE_OR_CAMERA),
            IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_no_telescope(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.NO_TELESCOPE_OR_CAMERA),
            IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    def test_may_submit_to_iotd_tp_process_no_acquisitions(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.NO_ACQUISITIONS),
            IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_may_submit_to_iotd_tp_process_no_acquisitions_but_northern_lights(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image(subject_type=SubjectType.NORTHERN_LIGHTS)
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines=DateTimeService.now()
        image.user.userprofile.save()

        self.assertEqual(
            (True, None), IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_may_submit_to_iotd_tp_process_no_acquisitions_but_noctilucent_clouds(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image(subject_type=SubjectType.NOCTILUCENT_CLOUDS)
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines=DateTimeService.now()
        image.user.userprofile.save()

        self.assertEqual(
            (True, None), IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_may_submit_to_iotd_tp_process_not_agreed_to_rules_and_guidelines(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)

        self.assertEqual(
            (False, MayNotSubmitToIotdTpReason.DID_NOT_AGREE_TO_RULES_AND_GUIDELINES),
            IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('django.contrib.auth.models.User.is_authenticated', new_callable=PropertyMock)
    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_may_submit_to_iotd_tp_process_all_ok(self, is_authenticated):
        is_authenticated.return_value = True

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines=DateTimeService.now()
        image.user.userprofile.save()

        self.assertEqual(
            (True, None), IotdService.may_submit_to_iotd_tp_process(image.user, image)
        )

    @patch('astrobin_apps_iotd.services.IotdService.may_submit_to_iotd_tp_process')
    def test_submit_to_iotd_tp_process_no_autosubmit(self, may_submit_to_iotd_tp_process):
        may_submit_to_iotd_tp_process.return_value = True, None

        submitter = Generators.user(groups=[GroupName.IOTD_STAFF, 'iotd_submitters'])
        reviewer = Generators.user(groups=[GroupName.IOTD_STAFF, GroupName.IOTD_REVIEWERS])
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())

        IotdService.submit_to_iotd_tp_process(image.user, image)

        self.assertTrue(image.designated_iotd_submitters.exists())
        self.assertTrue(submitter, image.designated_iotd_submitters.first())

        self.assertTrue(image.designated_iotd_reviewers.exists())
        self.assertTrue(reviewer, image.designated_iotd_reviewers.first())

        self.assertFalse(image.user.userprofile.auto_submit_to_iotd_tp_process)

    @patch('astrobin_apps_iotd.services.IotdService.may_submit_to_iotd_tp_process')
    def test_submit_to_iotd_tp_process_autosubmit(self, may_submit_to_iotd_tp_process):
        may_submit_to_iotd_tp_process.return_value = True, None

        submitter = Generators.user(groups=[GroupName.IOTD_STAFF, 'iotd_submitters'])
        reviewer = Generators.user(groups=[GroupName.IOTD_STAFF, GroupName.IOTD_REVIEWERS])
        image = Generators.image(submitted_for_iotd_tp_consideration = datetime.now())

        IotdService.submit_to_iotd_tp_process(image.user, image, True)

        self.assertTrue(image.designated_iotd_submitters.exists())
        self.assertTrue(submitter, image.designated_iotd_submitters.first())

        self.assertTrue(image.designated_iotd_reviewers.exists())
        self.assertTrue(reviewer, image.designated_iotd_reviewers.first())

        self.assertTrue(image.user.userprofile.auto_submit_to_iotd_tp_process)

    @patch('astrobin_apps_iotd.services.IotdService.may_submit_to_iotd_tp_process')
    def test_submit_to_iotd_tp_process_may_not(self, may_submit_to_iotd_tp_process):
        may_submit_to_iotd_tp_process.return_value = False, MayNotSubmitToIotdTpReason.ALREADY_SUBMITTED

        Generators.user(groups=[GroupName.IOTD_STAFF, 'iotd_submitters'])
        Generators.user(groups=[GroupName.IOTD_STAFF, GroupName.IOTD_REVIEWERS])
        image = Generators.image(submitted_for_iotd_tp_consideration=datetime.now())

        IotdService.submit_to_iotd_tp_process(image.user, image)

        self.assertFalse(image.designated_iotd_submitters.exists())
        self.assertFalse(image.designated_iotd_reviewers.exists())

    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_resubmit_for_iotd_tp_consideration(self):
        service = IotdService()

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines=DateTimeService.now()
        image.user.userprofile.save()

        submitter_1 = User.objects.create_user('submitter_1', 'submitter_1@test.com', 'password')
        submitter_2 = User.objects.create_user('submitter_2', 'submitter_2@test.com', 'password')
        submitters_group, created = Group.objects.get_or_create(name=GroupName.IOTD_SUBMITTERS)
        submitters_group.user_set.add(submitter_1, submitter_2)

        self.assertEqual((True, None), IotdService.may_submit_to_iotd_tp_process(image.user, image))

        service.submit_to_iotd_tp_process(image.user, image)
        time.sleep(.1)
        image.refresh_from_db()

        self.assertIsNotNone(image.submitted_for_iotd_tp_consideration)
        self.assertEqual(1, image.designated_iotd_submitters.count())

        designated_submitter = image.designated_iotd_submitters.first()
        previously_submitted = image.submitted_for_iotd_tp_consideration

        service.resubmit_to_iotd_tp_process(image.user, image)
        time.sleep(.1)
        image.refresh_from_db()

        self.assertIsNotNone(image.submitted_for_iotd_tp_consideration)
        self.assertGreater(image.submitted_for_iotd_tp_consideration, previously_submitted)
        self.assertEqual(1, image.designated_iotd_submitters.count())
        self.assertNotEqual(designated_submitter, image.designated_iotd_submitters.first())

    @patch('astrobin_apps_iotd.services.iotd_service.push_notification')
    def test_notify_about_upcoming_deadline_for_iotd_tp_submission_does_not_notify_recent_image(
            self, push_notification
    ):
        Generators.image()

        IotdService.notify_about_upcoming_deadline_for_iotd_tp_submission()

        self.assertFalse(push_notification.called)

    @patch('astrobin_apps_iotd.services.iotd_service.push_notification')
    def test_notify_about_upcoming_deadline_for_iotd_tp_submission_does_not_notify_image_too_late(
            self, push_notification
    ):
        Generators.image()

        Image.objects.all().update(
            published=DateTimeService.now() - timedelta(
                days=settings.IOTD_SUBMISSION_FOR_CONSIDERATION_WINDOW_DAYS -
                settings.IOTD_SUBMISSION_FOR_CONSIDERATION_REMINDER_DAYS -
                1
            )
        )

        IotdService.notify_about_upcoming_deadline_for_iotd_tp_submission()

        self.assertFalse(push_notification.called)

    @patch('astrobin_apps_iotd.services.iotd_service.push_notification')
    def test_notify_about_upcoming_deadline_for_iotd_tp_submission_does_not_notify_if_user_has_not_previous_submissions(
            self, push_notification
    ):
        Generators.image()

        Image.objects.all().update(
            published=DateTimeService.now() - timedelta(
                days=settings.IOTD_SUBMISSION_FOR_CONSIDERATION_WINDOW_DAYS -
                settings.IOTD_SUBMISSION_FOR_CONSIDERATION_REMINDER_DAYS
            )
        )

        IotdService.notify_about_upcoming_deadline_for_iotd_tp_submission()

        self.assertFalse(push_notification.called)

    @patch('astrobin_apps_iotd.services.iotd_service.push_notification')
    def test_notify_about_upcoming_deadline_for_iotd_tp_submission_does_not_notify_if_user_has_too_old_previous_submissions(
            self, push_notification
    ):
        image_1 = Generators.image()
        image_2 = Generators.image(user=image_1.user)

        Generators.premium_subscription(image_1.user, SubscriptionName.ULTIMATE_2020)
        image_1.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image_1.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image=image_1)

        may, _ = IotdService().submit_to_iotd_tp_process(image_1.user, image_1)

        image_1.published = DateTimeService.now() - timedelta(366)
        image_1.submitted_for_iotd_tp_consideration = DateTimeService.now() - timedelta(366)
        image_1.save()

        Image.objects.filter(pk=image_2.pk).update(
            published=DateTimeService.now() - timedelta(
                days=settings.IOTD_SUBMISSION_FOR_CONSIDERATION_WINDOW_DAYS -
                     settings.IOTD_SUBMISSION_FOR_CONSIDERATION_REMINDER_DAYS
            )
        )

        push_notification.reset_mock()

        IotdService.notify_about_upcoming_deadline_for_iotd_tp_submission()

        self.assertFalse(push_notification.called)

    @patch('astrobin_apps_iotd.services.iotd_service.push_notification')
    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_notify_about_upcoming_deadline_for_iotd_tp_submission_does_notify(
            self, push_notification
    ):
        image_1 = Generators.image()
        image_2 = Generators.image(user=image_1.user)

        Generators.premium_subscription(image_1.user, SubscriptionName.ULTIMATE_2020)
        image_1.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image_1.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image=image_1)
        image_1.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines=DateTimeService.now()
        image_1.user.userprofile.save()

        may, _ = IotdService().submit_to_iotd_tp_process(image_1.user, image_1)

        self.assertTrue(may)

        Image.objects.filter(pk=image_2.pk).update(
            published=DateTimeService.now() - timedelta(
                days=settings.IOTD_SUBMISSION_FOR_CONSIDERATION_WINDOW_DAYS -
                settings.IOTD_SUBMISSION_FOR_CONSIDERATION_REMINDER_DAYS
            )
        )

        push_notification.reset_mock()

        IotdService.notify_about_upcoming_deadline_for_iotd_tp_submission()

        push_notification.assert_has_calls(
            [
                mock.call([image_1.user], None, 'iotd_tp_submission_deadline', mock.ANY),
            ]
        )

    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_get_recently_expired_unsubmitted_images_too_late(self):
        service = IotdService()

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines=DateTimeService.now()
        image.user.userprofile.save()

        submitter_1 = User.objects.create_user('submitter_1', 'submitter_1@test.com', 'password')
        submitter_2 = User.objects.create_user('submitter_2', 'submitter_2@test.com', 'password')
        submitters_group, created = Group.objects.get_or_create(name=GroupName.IOTD_SUBMITTERS)
        submitters_group.user_set.add(submitter_1, submitter_2)

        self.assertEqual((True, None), IotdService.may_submit_to_iotd_tp_process(image.user, image))

        service.submit_to_iotd_tp_process(image.user, image)

        image.refresh_from_db()

        self.assertIsNotNone(image.submitted_for_iotd_tp_consideration)
        self.assertEqual(1, image.designated_iotd_submitters.count())

        image.submitted_for_iotd_tp_consideration = \
            DateTimeService.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) - timedelta(minutes=30)
        image.save()

        test_images = service.get_recently_expired_unsubmitted_images(timedelta(hours=1))

        self.assertEqual(0, test_images.count())

    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_get_recently_expired_unsubmitted_images_too_early(self):
        service = IotdService()

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines=DateTimeService.now()
        image.user.userprofile.save()

        submitter_1 = User.objects.create_user('submitter_1', 'submitter_1@test.com', 'password')
        submitter_2 = User.objects.create_user('submitter_2', 'submitter_2@test.com', 'password')
        submitters_group, created = Group.objects.get_or_create(name=GroupName.IOTD_SUBMITTERS)
        submitters_group.user_set.add(submitter_1, submitter_2)

        self.assertEqual((True, None), IotdService.may_submit_to_iotd_tp_process(image.user, image))

        service.submit_to_iotd_tp_process(image.user, image)

        image.refresh_from_db()

        self.assertIsNotNone(image.submitted_for_iotd_tp_consideration)
        self.assertEqual(1, image.designated_iotd_submitters.count())

        image.submitted_for_iotd_tp_consideration = \
            DateTimeService.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) + timedelta(minutes=120)
        image.save()

        test_images = service.get_recently_expired_unsubmitted_images(timedelta(hours=1))

        self.assertEqual(0, test_images.count())

    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_get_recently_expired_unsubmitted_images_right_time(self):
        service = IotdService()

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines=DateTimeService.now()
        image.user.userprofile.save()

        submitter_1 = User.objects.create_user('submitter_1', 'submitter_1@test.com', 'password')
        submitter_2 = User.objects.create_user('submitter_2', 'submitter_2@test.com', 'password')
        submitters_group, created = Group.objects.get_or_create(name=GroupName.IOTD_SUBMITTERS)
        submitters_group.user_set.add(submitter_1, submitter_2)

        self.assertEqual((True, None), IotdService.may_submit_to_iotd_tp_process(image.user, image))

        service.submit_to_iotd_tp_process(image.user, image)

        image.refresh_from_db()

        self.assertIsNotNone(image.submitted_for_iotd_tp_consideration)
        self.assertEqual(1, image.designated_iotd_submitters.count())

        image.submitted_for_iotd_tp_consideration = \
            DateTimeService.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) + timedelta(minutes=30)
        image.save()

        test_images = service.get_recently_expired_unsubmitted_images(timedelta(hours=1))

        self.assertEqual(1, test_images.count())


    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_get_recently_expired_unsubmitted_images_too_many_dismissals(self):
        service = IotdService()

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines=DateTimeService.now()
        image.user.userprofile.save()

        submitter_1 = User.objects.create_user('submitter_1', 'submitter_1@test.com', 'password')
        submitter_2 = User.objects.create_user('submitter_2', 'submitter_2@test.com', 'password')
        submitters_group, created = Group.objects.get_or_create(name=GroupName.IOTD_SUBMITTERS)
        submitters_group.user_set.add(submitter_1, submitter_2)

        self.assertEqual((True, None), IotdService.may_submit_to_iotd_tp_process(image.user, image))

        service.submit_to_iotd_tp_process(image.user, image)

        image.refresh_from_db()

        self.assertIsNotNone(image.submitted_for_iotd_tp_consideration)
        self.assertEqual(1, image.designated_iotd_submitters.count())

        image.submitted_for_iotd_tp_consideration = \
            DateTimeService.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) + timedelta(minutes=30)
        image.save()

        for x in range(0, settings.IOTD_MAX_DISMISSALS):
            IotdDismissedImage.objects.create(
                image=image,
                user=Generators.user()
            )

        test_images = service.get_recently_expired_unsubmitted_images(timedelta(hours=1))

        self.assertEqual(0, test_images.count())

    @override_settings(IOTD_LAST_RULES_UPDATE=datetime.now() - timedelta(days=1))
    def test_get_recently_expired_unsubmitted_images_too_many_submissions(self):
        service = IotdService()

        image = Generators.image()
        image.imaging_telescopes_2.add(EquipmentGenerators.telescope())
        image.imaging_cameras_2.add(EquipmentGenerators.camera())
        Generators.deep_sky_acquisition(image)
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines=DateTimeService.now()
        image.user.userprofile.save()

        submitter_1 = User.objects.create_user('submitter_1', 'submitter_1@test.com', 'password')
        submitter_2 = User.objects.create_user('submitter_2', 'submitter_2@test.com', 'password')
        submitters_group, created = Group.objects.get_or_create(name=GroupName.IOTD_SUBMITTERS)
        submitters_group.user_set.add(submitter_1, submitter_2)

        self.assertEqual((True, None), IotdService.may_submit_to_iotd_tp_process(image.user, image))

        service.submit_to_iotd_tp_process(image.user, image)

        image.refresh_from_db()

        self.assertIsNotNone(image.submitted_for_iotd_tp_consideration)
        self.assertEqual(1, image.designated_iotd_submitters.count())

        image.submitted_for_iotd_tp_consideration = \
            DateTimeService.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) + timedelta(minutes=30)
        image.save()

        for x in range(0, settings.IOTD_MAX_DISMISSALS):
            IotdGenerators.submission(image=image)

        test_images = service.get_recently_expired_unsubmitted_images(timedelta(hours=1))

        self.assertEqual(0, test_images.count())
