import datetime

from django.test import TestCase, override_settings

from astrobin.tests.generators import Generators
from astrobin_apps_iotd.permissions import may_unelect_iotd
from astrobin_apps_iotd.tests.iotd_generators import IotdGenerators
from common.services import DateTimeService


@override_settings(
    IOTD_SUBMISSION_MIN_PROMOTIONS=1,
    IOTD_REVIEW_MIN_PROMOTIONS=1
)
class IotdPermissionsTest(TestCase):
    def test_may_unelect_iotd_yesterday(self):
        user = Generators.user()
        Generators.premium_subscription(user, 'AstroBin Ultimate 2020+')
        image = Generators.image(user=user)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        iotd = IotdGenerators.iotd(image=image, date=DateTimeService.today() - datetime.timedelta(1))

        self.assertEqual(
            (False, 'You cannot unelect a past or current IOTD.'), may_unelect_iotd(iotd.judge, iotd.image)
        )

    def test_may_unelect_iotd_today(self):
        user = Generators.user()
        Generators.premium_subscription(user, 'AstroBin Ultimate 2020+')
        image = Generators.image(user=user)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        iotd = IotdGenerators.iotd(image=image, date=DateTimeService.today())

        self.assertEqual((False, 'You cannot unelect a past or current IOTD.'), may_unelect_iotd(iotd.judge, iotd.image))

    def test_may_unelect_iotd_tomorrow(self):
        user = Generators.user()
        Generators.premium_subscription(user, 'AstroBin Ultimate 2020+')
        image = Generators.image(user=user)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        iotd = IotdGenerators.iotd(image=image, date=DateTimeService.today() + datetime.timedelta(1))

        self.assertEqual(
            (False, 'You cannot unelect an IOTD that is due tomorrow (UTC).'), may_unelect_iotd(iotd.judge, iotd.image)
        )

    def test_may_unelect_iotd_day_after_tomorrow(self):
        user = Generators.user()
        Generators.premium_subscription(user, 'AstroBin Ultimate 2020+')
        image = Generators.image(user=user)

        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        iotd = IotdGenerators.iotd(image=image, date=DateTimeService.today() + datetime.timedelta(2))

        self.assertEqual((True, None), may_unelect_iotd(iotd.judge, iotd.image))
