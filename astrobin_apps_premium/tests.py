# Django
from django.contrib.auth.models import User, Group
from django.test import TestCase

# Third party
from subscription.models import Subscription, UserSubscription

# Premium
from astrobin_apps_premium.utils import *
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import *


class SubscriptionsTest(TestCase):
    def test_subscription_validity(self):
        u = User.objects.create_user(
            username = 'test', email='test@test.com', password = 'password')
        g, created = Group.objects.get_or_create(name = "premium")
        s, created = Subscription.objects.get_or_create(
            name = "AstroBin Premium",
            price = 1,
            group = g,
            category = "premium")
        us, created = UserSubscription.objects.get_or_create(
            user = u,
            subscription = s)
        us.subscribe()

        self.assertEqual(premium_get_usersubscription(u), us)
        self.assertEqual(premium_get_valid_usersubscription(u), us)
        self.assertEqual(premium_get_invalid_usersubscription(u), None)
        self.assertEqual(premium_user_has_subscription(u), True)
        self.assertEqual(premium_user_has_valid_subscription(u), True)
        self.assertEqual(premium_user_has_invalid_subscription(u), False)

        self.assertEqual(is_premium(u), True)

        us.unsubscribe()
        us.delete()
        s.delete()
        g.delete()
        u.delete()

        # Test Lite

        u = User.objects.create_user(
            username = 'test', email='test@test.com', password = 'password')
        g, created = Group.objects.get_or_create(name = "lite")
        s, created = Subscription.objects.get_or_create(
            name = "AstroBin Lite",
            price = 1,
            group = g,
            category = "premium")
        us, created = UserSubscription.objects.get_or_create(
            user = u,
            subscription = s)
        us.subscribe()

        self.assertEqual(is_lite(u), True)

        # Test free
        us.unsubscribe()
        self.assertEqual(is_free(u), True)

        us.delete()
        s.delete()
        g.delete()
        u.delete()
