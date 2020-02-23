from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.test import TestCase
from subscription.models import Subscription, UserSubscription

from astrobin.tests.generators import Generators
from astrobin_apps_premium.utils import premium_get_valid_usersubscription


class CommandsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'password', date_joined=date(2020, 1, 1))

        self.lite = Subscription.objects.create(
            name='AstroBin Lite',
            price=18,
            trial_period=0,
            trial_unit=None,
            recurrence_period=0,
            recurrence_unit=None,
            group=Group.objects.create(name='astrobin_lite'),
            category='premium')

        self.lite_autorenew = Subscription.objects.create(
            name='AstroBin Lite (autorenew)',
            price=18,
            trial_period=0,
            trial_unit=None,
            recurrence_period=1,
            recurrence_unit="Y",
            group=Group.objects.get(name='astrobin_lite'),
            category='premium')

        self.premium = Subscription.objects.create(
            name='AstroBin Premium',
            price=36,
            trial_period=0,
            trial_unit=None,
            recurrence_period=0,
            recurrence_unit=None,
            group=Group.objects.create(name='astrobin_premium'),
            category='premium')

        self.premium_autorenew = Subscription.objects.create(
            name='AstroBin Premium (autorenew)',
            price=36,
            trial_period=0,
            trial_unit=None,
            recurrence_period=1,
            recurrence_unit="Y",
            group=Group.objects.get(name='astrobin_premium'),
            category='premium')

        self.user.image_set.add(Generators.image())

    def test_upgrade_free_to_premium_dry_run(self):
        call_command('upgrade_free_and_lite_to_premium', dry_run=True)
        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertIsNone(user_subscription)

    def test_upgrade_free_to_premium(self):
        call_command('upgrade_free_and_lite_to_premium')
        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertEquals("AstroBin Premium", user_subscription.subscription.name)
        self.assertEquals(date.today() + relativedelta(years=1), user_subscription.expires)

    def test_upgrade_free_to_premium_when_joined_after_data_loss(self):
        self.user.date_joined = date(2020, 2, 16)
        self.user.save()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertIsNone(user_subscription)

    def test_upgrade_free_to_premium_when_deleted(self):
        self.user.userprofile.delete()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertIsNone(user_subscription)

    def test_upgrade_free_to_premium_when_no_images(self):
        self.user.image_set.all().delete()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertIsNone(user_subscription)

    def test_upgrade_lite_to_premium(self):
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.lite,
            active=True,
            expires=date.today() + relativedelta(months=1))
        user_subscription.subscribe()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertEquals("AstroBin Premium", user_subscription.subscription.name)
        self.assertEquals(date.today() + relativedelta(years=1), user_subscription.expires)

    def test_upgrade_lite_autorenew_to_premium(self):
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.lite_autorenew,
            active=True,
            expires=date.today() + relativedelta(months=1))
        user_subscription.subscribe()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertEquals("AstroBin Premium", user_subscription.subscription.name)
        self.assertEquals(date.today() + relativedelta(years=1), user_subscription.expires)

    def test_upgrade_expired_lite_to_premium(self):
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.lite,
            active=True,
            expires=date.today() - relativedelta(months=1))
        user_subscription.subscribe()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertEquals("AstroBin Premium", user_subscription.subscription.name)
        self.assertEquals(date.today() + relativedelta(years=1), user_subscription.expires)

    def test_upgrade_expired_lite_autorenew_to_premium(self):
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.lite_autorenew,
            active=True,
            expires=date.today() - relativedelta(months=1))
        user_subscription.subscribe()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertEquals("AstroBin Premium", user_subscription.subscription.name)
        self.assertEquals(date.today() + relativedelta(years=1), user_subscription.expires)

    def test_upgrade_expired_premium_to_premium(self):
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.premium,
            active=True,
            expires=date.today() - relativedelta(months=1))
        user_subscription.subscribe()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertEquals("AstroBin Premium", user_subscription.subscription.name)
        self.assertEquals(date.today() + relativedelta(years=1), user_subscription.expires)

    def test_upgrade_valid_premium_to_premium_not_altered(self):
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.premium,
            active=True,
            expires=date.today() + relativedelta(months=1))
        user_subscription.subscribe()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertEquals("AstroBin Premium", user_subscription.subscription.name)
        self.assertEquals(date.today() + relativedelta(months=1), user_subscription.expires)

    def test_upgrade_expired_premium_autorenew_to_premium(self):
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.premium_autorenew,
            active=True,
            expires=date.today() - relativedelta(months=1))
        user_subscription.subscribe()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertEquals("AstroBin Premium", user_subscription.subscription.name)
        self.assertEquals(date.today() + relativedelta(years=1), user_subscription.expires)

    def test_upgrade_valid_premium_autorenew_to_premium_not_altered(self):
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.premium_autorenew,
            active=True,
            expires=date.today() + relativedelta(months=1))
        user_subscription.subscribe()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertEquals("AstroBin Premium (autorenew)", user_subscription.subscription.name)
        self.assertEquals(date.today() + relativedelta(months=1), user_subscription.expires)

    def test_upgrade_lite_with_past_premium_to_premium(self):
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.premium_autorenew,
            active=False,
            expires=date.today() - relativedelta(months=1))
        user_subscription.subscribe()

        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.lite,
            active=True,
            expires=date.today() + relativedelta(months=1))
        user_subscription.subscribe()

        call_command('upgrade_free_and_lite_to_premium')

        user_subscription = premium_get_valid_usersubscription(self.user)
        self.assertEquals("AstroBin Premium", user_subscription.subscription.name)
        self.assertEquals(date.today() + relativedelta(years=1), user_subscription.expires)
