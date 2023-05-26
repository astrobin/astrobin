from datetime import date, timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from subscription.models import Subscription, Transaction
from subscription.utils import extend_date_by

from astrobin.tests.generators import Generators
from astrobin_apps_payments.services.stripe_webhook_service import StripeWebhookService
from astrobin_apps_payments.tests.stripe_generators import StripeGenerators
from astrobin_apps_premium.services.premium_service import PremiumService, SubscriptionName


class StripeWebhookServiceUltimateOnceFirstOrderTest(TestCase):
    def setUp(self):
        self.subscription, created = Subscription.objects.get_or_create(
            name=SubscriptionName.ULTIMATE_2020.value,
            currency="CHF",
            price=20,
            trial_period=0,
            trial_unit=None,
            recurrence_period=None,
            recurrence_unit=None,
            group=Group.objects.get_or_create(name='astrobin_ultimate_2020')[0],
            category='premium_autorenew'
        )

    def test_first_order(self):
        user = Generators.user(email="astrobin@astrobin.com")
        e = StripeGenerators.event

        StripeWebhookService.process_event(e('ultimate_once_first_order/payment_intent.created'))
        StripeWebhookService.process_event(e('ultimate_once_first_order/customer.created'))
        StripeWebhookService.process_event(e('ultimate_once_first_order/payment_intent.succeeded'))
        StripeWebhookService.process_event(e('ultimate_once_first_order/charge.succeeded'))
        StripeWebhookService.process_event(e('ultimate_once_first_order/checkout.session.completed'))

        user.userprofile.refresh_from_db()

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.expires, extend_date_by(date.today(), 1, 'Y'))
        self.assertEqual(valid_subscription.subscription, self.subscription)
        self.assertIsNotNone(user.userprofile.stripe_customer_id)
        self.assertIsNone(user.userprofile.stripe_subscription_id)
        self.assertEqual(
            1,
            Transaction.objects.filter(
                user=user,
                subscription=self.subscription,
                event='one-time payment',
                amount=self.subscription.price,
            ).count()
        )

    def test_renewal(self):
        user = Generators.user(email="astrobin@astrobin.com")
        e = StripeGenerators.event

        user_subscription = Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        user_subscription.expires = date.today()
        user_subscription.save()

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.expires, date.today())
        self.assertEqual(valid_subscription.subscription, self.subscription)

        StripeWebhookService.process_event(e('ultimate_once_renewal/payment_intent.created'))
        StripeWebhookService.process_event(e('ultimate_once_renewal/payment_intent.succeeded'))
        StripeWebhookService.process_event(e('ultimate_once_renewal/charge.succeeded'))
        StripeWebhookService.process_event(e('ultimate_once_renewal/checkout.session.completed'))

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.expires, extend_date_by(date.today(), 1, 'Y'))
        self.assertEqual(valid_subscription.subscription, self.subscription)
        self.assertEqual(
            1,
            Transaction.objects.filter(
                user=user,
                subscription=self.subscription,
                event='one-time payment',
                amount=self.subscription.price,
            ).count()
        )

    def test_renewal_before_expiration(self):
        user = Generators.user(email="astrobin@astrobin.com")
        e = StripeGenerators.event

        user_subscription = Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        user_subscription.expires = date.today() + timedelta(days=30)
        user_subscription.save()

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.expires, date.today() + timedelta(days=30))
        self.assertEqual(valid_subscription.subscription, self.subscription)

        StripeWebhookService.process_event(e('ultimate_once_renewal/payment_intent.created'))
        StripeWebhookService.process_event(e('ultimate_once_renewal/payment_intent.succeeded'))
        StripeWebhookService.process_event(e('ultimate_once_renewal/charge.succeeded'))
        StripeWebhookService.process_event(e('ultimate_once_renewal/checkout.session.completed'))

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.expires, extend_date_by(date.today(), 1, 'Y') + timedelta(days=30))
        self.assertEqual(valid_subscription.subscription, self.subscription)
        self.assertEqual(
            1,
            Transaction.objects.filter(
                user=user,
                subscription=self.subscription,
                event='one-time payment',
                amount=self.subscription.price,
            ).count()
        )
