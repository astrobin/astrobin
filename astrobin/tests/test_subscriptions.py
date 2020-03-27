# Django
from django.contrib.auth.models import User, Group
from django.test import TestCase
# Third party
from django.urls import reverse
from subscription.models import Subscription, UserSubscription

# AstroBin
from astrobin.templatetags.tags import (
    valid_subscriptions,
    has_valid_subscription,
    has_valid_subscription_in_category,
    get_premium_subscription_expiration,
    has_subscription_by_name,
    get_usersubscription_by_name)


class SubscriptionsTest(TestCase):
    def test_subscription_validity(self):
        with self.settings(PREMIUM_ENABLED=True):
            u = User.objects.create_user(
                username='test', email='test@test.com', password='password')
            g, created = Group.objects.get_or_create(name="astrobin_premium")
            s, created = Subscription.objects.get_or_create(
                name="AstroBin Premium",
                price=1,
                group=g,
                category="premium")
            us, created = UserSubscription.objects.get_or_create(
                user=u,
                subscription=s)

            us.subscribe()

            self.assertEqual(valid_subscriptions(u), [s])
            self.assertEqual(has_valid_subscription(u, s.pk), True)
            self.assertEqual(has_valid_subscription_in_category(u, "premium"), True)
            self.assertEqual(get_premium_subscription_expiration(u), us.expires)
            self.assertEqual(has_subscription_by_name(u, "AstroBin Premium"), True)
            self.assertEqual(get_usersubscription_by_name(u, "AstroBin Premium"), us)

            us.delete()
            s.delete()
            g.delete()
            u.delete()

    def test_offer_subscription_validity(self):
        with self.settings(PREMIUM_ENABLED=True):
            u = User.objects.create_user(
                username='test', email='test@test.com', password='password')
            g, created = Group.objects.get_or_create(name="astrobin_premium")
            s, created = Subscription.objects.get_or_create(
                name="AstroBin Premium 20% discount",
                price=1,
                group=g,
                category="premium_offer_discount_20")
            us, created = UserSubscription.objects.get_or_create(
                user=u,
                subscription=s)

            us.subscribe()

            self.assertEqual(valid_subscriptions(u), [s])
            self.assertEqual(has_valid_subscription(u, s.pk), True)
            self.assertEqual(has_valid_subscription_in_category(u, "premium"), True)
            self.assertEqual(get_premium_subscription_expiration(u), us.expires)
            self.assertEqual(has_subscription_by_name(u, "AstroBin Premium 20% discount"), True)
            self.assertEqual(get_usersubscription_by_name(u, "AstroBin Premium 20% discount"), us)

            us.delete()
            s.delete()
            g.delete()
            u.delete()
