from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_premium.models import DataLossCompensationRequest
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_ultimate_2020, is_premium, is_lite
from astrobin_apps_premium.tasks import reactivate_previous_subscription_when_ultimate_compensation_expires

class TestReactivatePreviousSubscription(TestCase):
    def test_without_compensation_request(self):
        user = User.objects.create_user(username="test", password="test")
        premium = Generators.premium_subscription(user, "AstroBin Premium (autorenew)")
        ultimate = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        premium.expires = date.today() + timedelta(days=30)
        premium.unsubscribe()

        ultimate.expires = date.today()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

        reactivate_previous_subscription_when_ultimate_compensation_expires.apply()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

    def test_with_compensation_request_not_affected(self):
        user = User.objects.create_user(username="test", password="test")
        premium = Generators.premium_subscription(user, "AstroBin Premium (autorenew)")
        ultimate = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        premium.expires = date.today() + timedelta(days=30)
        premium.unsubscribe()

        ultimate.expires = date.today()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

        DataLossCompensationRequest.objects.create(
            user=user,
            requested_compensation="NOT_AFFECTED"
        )

        reactivate_previous_subscription_when_ultimate_compensation_expires.apply()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

    def test_with_compensation_request_not_required(self):
        user = User.objects.create_user(username="test", password="test")
        premium = Generators.premium_subscription(user, "AstroBin Premium (autorenew)")
        ultimate = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        premium.expires = date.today() + timedelta(days=30)
        premium.unsubscribe()
        premium.save()

        ultimate.expires = date.today()
        ultimate.save()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

        DataLossCompensationRequest.objects.create(
            user=user,
            requested_compensation="NOT_REQUIRED"
        )

        reactivate_previous_subscription_when_ultimate_compensation_expires.apply()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

    def test_with_compensation_1_mo(self):
        user = User.objects.create_user(username="test", password="test")
        premium = Generators.premium_subscription(user, "AstroBin Premium (autorenew)")
        ultimate = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        premium.expires = date.today() + timedelta(days=30)
        premium.unsubscribe()
        premium.save()

        ultimate.expires = date.today()
        ultimate.save()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

        DataLossCompensationRequest.objects.create(
            user=user,
            requested_compensation="1_MO_ULTIMATE"
        )

        reactivate_previous_subscription_when_ultimate_compensation_expires.apply()

        self.assertFalse(is_ultimate_2020(user))
        self.assertTrue(is_premium(user))

    def test_with_compensation_3_mo(self):
        user = User.objects.create_user(username="test", password="test")
        premium = Generators.premium_subscription(user, "AstroBin Premium (autorenew)")
        ultimate = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        premium.expires = date.today() + timedelta(days=30)
        premium.unsubscribe()
        premium.save()

        ultimate.expires = date.today()
        ultimate.save()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

        DataLossCompensationRequest.objects.create(
            user=user,
            requested_compensation="3_MO_ULTIMATE"
        )

        reactivate_previous_subscription_when_ultimate_compensation_expires.apply()

        self.assertFalse(is_ultimate_2020(user))
        self.assertTrue(is_premium(user))

    def test_with_compensation_6_mo(self):
        user = User.objects.create_user(username="test", password="test")
        premium = Generators.premium_subscription(user, "AstroBin Premium (autorenew)")
        ultimate = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        premium.expires = date.today() + timedelta(days=30)
        premium.unsubscribe()
        premium.save()

        ultimate.expires = date.today()
        ultimate.save()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

        DataLossCompensationRequest.objects.create(
            user=user,
            requested_compensation="6_MO_ULTIMATE"
        )

        reactivate_previous_subscription_when_ultimate_compensation_expires.apply()

        self.assertFalse(is_ultimate_2020(user))
        self.assertTrue(is_premium(user))

    def test_with_compensation_1_mo_and_premium_autorenew(self):
        user = User.objects.create_user(username="test", password="test")
        premium = Generators.premium_subscription(user, "AstroBin Premium (autorenew)")
        ultimate = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        premium.expires = date.today() + timedelta(days=30)
        premium.unsubscribe()
        premium.save()

        ultimate.expires = date.today()
        ultimate.save()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

        DataLossCompensationRequest.objects.create(
            user=user,
            requested_compensation="1_MO_ULTIMATE"
        )

        reactivate_previous_subscription_when_ultimate_compensation_expires.apply()

        self.assertFalse(is_ultimate_2020(user))
        self.assertTrue(is_premium(user))

    def test_with_compensation_1_mo_and_premium_non_autorenew(self):
        user = User.objects.create_user(username="test", password="test")
        premium = Generators.premium_subscription(user, "AstroBin Premium")
        ultimate = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        premium.expires = date.today() + timedelta(days=30)
        premium.unsubscribe()
        premium.save()

        ultimate.expires = date.today()
        ultimate.save()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_premium(user))

        DataLossCompensationRequest.objects.create(
            user=user,
            requested_compensation="1_MO_ULTIMATE"
        )

        reactivate_previous_subscription_when_ultimate_compensation_expires.apply()

        self.assertFalse(is_ultimate_2020(user))
        self.assertTrue(is_premium(user))

    def test_with_compensation_1_mo_and_lite(self):
        user = User.objects.create_user(username="test", password="test")
        premium = Generators.premium_subscription(user, "AstroBin Lite (autorenew)")
        ultimate = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        premium.expires = date.today() + timedelta(days=30)
        premium.unsubscribe()
        premium.save()

        ultimate.expires = date.today()
        ultimate.save()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_lite(user))

        DataLossCompensationRequest.objects.create(
            user=user,
            requested_compensation="1_MO_ULTIMATE"
        )

        reactivate_previous_subscription_when_ultimate_compensation_expires.apply()

        self.assertFalse(is_ultimate_2020(user))
        self.assertTrue(is_lite(user))

    def test_with_compensation_1_mo_and_lite_non_autorenew(self):
        user = User.objects.create_user(username="test", password="test")
        premium = Generators.premium_subscription(user, "AstroBin Lite")
        ultimate = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        premium.expires = date.today() + timedelta(days=30)
        premium.unsubscribe()
        premium.save()

        ultimate.expires = date.today()
        ultimate.save()

        self.assertTrue(is_ultimate_2020(user))
        self.assertFalse(is_lite(user))

        DataLossCompensationRequest.objects.create(
            user=user,
            requested_compensation="1_MO_ULTIMATE"
        )

        reactivate_previous_subscription_when_ultimate_compensation_expires.apply()

        self.assertFalse(is_ultimate_2020(user))
        self.assertTrue(is_lite(user))
