import json

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse
from subscription.models import Subscription, UserSubscription

from astrobin.templatetags.tags import (
    valid_subscriptions,
    has_valid_subscription,
    has_valid_subscription_in_category,
    get_paid_subscription_expiration,
    has_subscription_by_name,
    get_usersubscription_by_name)
from astrobin.tests.generators import Generators
from astrobin_apps_premium.services.premium_service import PremiumService, SubscriptionName


class SubscriptionsTest(TestCase):
    def test_subscription_validity(self):
        with self.settings(PREMIUM_ENABLED=True):
            u = User.objects.create_user(
                username='test', email='test@test.com', password='password')
            g, created = Group.objects.get_or_create(name="astrobin_premium")
            s, created = Subscription.objects.get_or_create(
                name=SubscriptionName.PREMIUM_CLASSIC,
                price=1,
                group=g,
                category="premium")
            us, created = UserSubscription.objects.get_or_create(
                user=u,
                subscription=s)

            us.subscribe()

            valid_subscription = PremiumService(u).get_valid_usersubscription()

            self.assertEqual(valid_subscriptions(u), [s])
            self.assertEqual(has_valid_subscription(u, s.pk), True)
            self.assertEqual(has_valid_subscription_in_category(u, "premium"), True)
            self.assertEqual(get_paid_subscription_expiration(valid_subscription), us.expires)
            self.assertEqual(has_subscription_by_name(u, SubscriptionName.PREMIUM_CLASSIC), True)
            self.assertEqual(get_usersubscription_by_name(u, SubscriptionName.PREMIUM_CLASSIC), us)

            us.delete()
            s.delete()
            g.delete()
            u.delete()

    def test_usersubscription_api(self):
        user = Generators.user()
        Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        self.client.login(username=user.username, password=user.password)
        response = self.client.get('%s?user=%d' % (reverse('usersubscription-list'), user.pk))
        response_json = json.loads(response.content)
        self.assertEqual(1, len(response_json))
        self.assertEqual(user.pk, response_json[0]['user'])

    def test_offer_subscription_validity(self):
        with self.settings(PREMIUM_ENABLED=True):
            u = User.objects.create_user(
                username='test', email='test@test.com', password='password')
            g, created = Group.objects.get_or_create(name="astrobin_premium")
            s, created = Subscription.objects.get_or_create(
                name=SubscriptionName.PREMIUM_CLASSIC_20_PERCENT_DISCOUNT,
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
            self.assertEqual(
                get_paid_subscription_expiration(PremiumService(u).get_valid_usersubscription()), us.expires
            )
            self.assertEqual(has_subscription_by_name(u, SubscriptionName.PREMIUM_CLASSIC_20_PERCENT_DISCOUNT), True)
            self.assertEqual(get_usersubscription_by_name(u, SubscriptionName.PREMIUM_CLASSIC_20_PERCENT_DISCOUNT), us)

            us.delete()
            s.delete()
            g.delete()
            u.delete()
