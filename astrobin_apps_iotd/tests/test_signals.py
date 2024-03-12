from django.test import TestCase, override_settings

from astrobin.tests.generators import Generators
from astrobin_apps_iotd.tests.iotd_generators import IotdGenerators
from common.constants import GroupName
from common.services import DateTimeService


class IotdSignalsTest(TestCase):
    @override_settings(IOTD_MIN_PROMOTIONS_PER_PERIOD='1/7')
    def test_submitter_insufficiently_active_reminders_reset(self):
        user = Generators.user()

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter.userprofile.insufficiently_active_iotd_staff_member_reminders_sent = 2
        submitter.userprofile.save(keep_deleted=True)

        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=DateTimeService.now())
        image.designated_iotd_submitters.add(submitter)

        IotdGenerators.submission(submitter=submitter, image=image)

        submitter.userprofile.refresh_from_db()

        self.assertEqual(submitter.userprofile.insufficiently_active_iotd_staff_member_reminders_sent, 0)

    @override_settings(IOTD_MIN_PROMOTIONS_PER_PERIOD='2/7')
    def test_submitter_insufficiently_active_reminders_no_reset(self):
        user = Generators.user()

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        submitter.userprofile.insufficiently_active_iotd_staff_member_reminders_sent = 2
        submitter.userprofile.save(keep_deleted=True)

        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=DateTimeService.now())
        image.designated_iotd_submitters.add(submitter)

        IotdGenerators.submission(submitter=submitter, image=image)

        submitter.userprofile.refresh_from_db()

        self.assertEqual(submitter.userprofile.insufficiently_active_iotd_staff_member_reminders_sent, 2)

    @override_settings(
        IOTD_MIN_PROMOTIONS_PER_PERIOD='1/7',
        IOTD_SUBMISSION_MIN_PROMOTIONS=1
    )
    def test_reviewer_insufficiently_active_reminders_reset(self):
        user = Generators.user()

        submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
        reviewer = Generators.user(groups=[GroupName.IOTD_REVIEWERS])
        reviewer.userprofile.insufficiently_active_iotd_staff_member_reminders_sent = 2
        reviewer.userprofile.save(keep_deleted=True)

        image = Generators.image(user=user, submitted_for_iotd_tp_consideration=DateTimeService.now())
        image.designated_iotd_submitters.add(submitter)
        image.designated_iotd_submitters.add(reviewer)

        IotdGenerators.submission(submitter=submitter, image=image)
        IotdGenerators.vote(reviewer=reviewer, image=image)

        reviewer.userprofile.refresh_from_db()

        self.assertEqual(reviewer.userprofile.insufficiently_active_iotd_staff_member_reminders_sent, 0)
