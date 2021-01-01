from datetime import timedelta, date, datetime

from django.conf import settings
from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.tests.iotd_generators import IotdGenerators


class IotdServiceTest(TestCase):
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
