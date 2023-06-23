import datetime
from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from subscription.models import Subscription, Transaction
from subscription.utils import extend_date_by

from astrobin.tests.generators import Generators
from astrobin_apps_payments.services.stripe_webhook_service import StripeWebhookService
from astrobin_apps_payments.tests.stripe_generators import StripeGenerators
from astrobin_apps_premium.services.premium_service import PremiumService, SubscriptionName


class StripeWebhookServiceUltimateYearlyTest(TestCase):
    def setUp(self):
        self.subscription, created = Subscription.objects.get_or_create(
            name=SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY.value,
            currency="CHF",
            price=20,
            trial_period=0,
            trial_unit=None,
            recurrence_period=1,
            recurrence_unit='Y',
            group=Group.objects.get_or_create(name='astrobin_ultimate_2020')[0],
            category='ultimate_autorenew'
        )

        Subscription.objects.get_or_create(
            name=SubscriptionName.PREMIUM_2020_AUTORENEW_YEARLY.value,
            currency="CHF",
            price=20,
            trial_period=0,
            trial_unit=None,
            recurrence_period=1,
            recurrence_unit='Y',
            group=Group.objects.get_or_create(name='astrobin_premium_2020')[0],
            category='ultimate_autorenew'
        )

    def test_first_order(self):
        user = Generators.user(email="astrobin@astrobin.com")
        e = StripeGenerators.event

        StripeWebhookService.process_event(e('ultimate_yearly_first_order/charge.succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/payment_method.attached'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/customer.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/customer.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/invoice.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/customer.subscription.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/invoice.finalized'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/invoice.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/invoice.paid'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/invoice.payment_succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/customer.subscription.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/payment_intent.succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/payment_intent.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_first_order/checkout.session.completed'))

        user.userprofile.refresh_from_db()

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.expires, date(2024, 5, 26))
        self.assertFalse(valid_subscription.cancelled)
        self.assertEqual(valid_subscription.subscription, self.subscription)
        self.assertIsNotNone(user.userprofile.stripe_customer_id)
        self.assertIsNotNone(user.userprofile.stripe_subscription_id)
        self.assertEqual(
            1,
            Transaction.objects.filter(
                user=user,
                subscription=self.subscription,
                event='subscription payment',
                amount=22.50,
            ).count()
        )

    def test_cancellation(self):
        user = Generators.user(email="astrobin@astrobin.com")
        user.userprofile.stripe_customer_id = 'STRIPE_CUSTOMER_ID'
        user.userprofile.save()

        e = StripeGenerators.event

        user_subscription = Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY)

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.subscription, self.subscription)
        self.assertFalse(valid_subscription.cancelled)

        StripeWebhookService.process_event(e('ultimate_yearly_cancellation/billing_portal.session.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_cancellation/customer.subscription.updated'))

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))

        user_subscription.refresh_from_db()
        self.assertTrue(user_subscription.cancelled)

    def test_renewal(self):
        user = Generators.user(email="astrobin@astrobin.com")
        user.userprofile.stripe_customer_id = 'STRIPE_CUSTOMER_ID'
        user.userprofile.save()

        e = StripeGenerators.event

        user_subscription = Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY)
        user_subscription.expires = extend_date_by(date.today(), 1, 'Y')
        user_subscription.save()

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.subscription, self.subscription)
        self.assertFalse(valid_subscription.cancelled)

        StripeWebhookService.process_event(e('ultimate_yearly_renewal/payment_intent.succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_renewal/charge.succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_renewal/customer.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_renewal/invoice.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_renewal/invoice.paid'))
        StripeWebhookService.process_event(e('ultimate_yearly_renewal/invoice.payment_succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_renewal/invoice.finalized'))
        StripeWebhookService.process_event(e('ultimate_yearly_renewal/invoice.upcoming'))
        StripeWebhookService.process_event(e('ultimate_yearly_renewal/invoice.created'))

        customer_subscription_updated = e('ultimate_yearly_renewal/customer.subscription.updated')
        current_period_end = extend_date_by(date.today(), 2, 'Y')
        time_obj = datetime.time()
        datetime_obj = datetime.datetime.combine(current_period_end, time_obj)
        unix_timestamp = int(datetime_obj.timestamp())
        customer_subscription_updated['data']['object']['current_period_end'] = unix_timestamp
        StripeWebhookService.process_event(customer_subscription_updated)

        user_subscription.refresh_from_db()

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.subscription, self.subscription)
        self.assertEqual(valid_subscription.expires, current_period_end)
        self.assertFalse(valid_subscription.cancelled)

    def test_failed_payment_then_succeeded(self):
        user = Generators.user(email="astrobin@astrobin.com")
        user.userprofile.stripe_customer_id = 'STRIPE_CUSTOMER_ID'
        user.userprofile.save()

        e = StripeGenerators.event

        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/charge.failed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.finalized'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.payment_failed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.updated.2'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/payment_intent.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/payment_intent.payment_failed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.subscription.created'))

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertFalse(PremiumService.is_ultimate_2020(valid_subscription))

        # After failing to pay, the customer succeeds.

        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.subscription.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/checkout.session.completed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/payment_method.attached'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/charge.succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.updated.3'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.updated.2'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.payment_succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.paid'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.subscription.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/payment_intent.succeeded'))

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertFalse(valid_subscription.cancelled)

    def test_failed_payment_then_succeeded_bad_order(self):
        # In this test, customer.subscription.updated comes before customer.subscription.created.
        # This would be an issue because on customer.subscription.created, the subscription is incomplete.
        user = Generators.user(email="astrobin@astrobin.com")
        user.userprofile.stripe_customer_id = 'STRIPE_CUSTOMER_ID'
        user.userprofile.save()

        e = StripeGenerators.event

        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/charge.failed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.finalized'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.payment_failed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.updated.2'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/payment_intent.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/payment_intent.payment_failed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.subscription.created'))

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertFalse(PremiumService.is_ultimate_2020(valid_subscription))

        # After failing to pay, the customer succeeds.

        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/checkout.session.completed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/payment_method.attached'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/charge.succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.updated.3'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.updated.2'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.payment_succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/invoice.paid'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.subscription.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/payment_intent.succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment/customer.subscription.created'))

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))

    def test_failed_payment_then_succeeded_then_changed_subscription(self):
        # In this test the user attempts to buy Ultimate, fails to pay, then buys Premium.
        user = Generators.user(email="astrobin@astrobin.com")
        user.userprofile.stripe_customer_id = 'STRIPE_CUSTOMER_ID'
        user.userprofile.save()

        e = StripeGenerators.event

        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/charge.failed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/customer.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/customer.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/invoice.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/invoice.finalized'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/invoice.payment_failed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/customer.updated.2'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/invoice.updated'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/payment_intent.created'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/payment_intent.payment_failed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/customer.subscription.created'))

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertFalse(PremiumService.is_ultimate_2020(valid_subscription))

        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/checkout.session.completed'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/payment_method.attached'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/charge.succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/customer.updated.3'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/invoice.updated.2'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/invoice.payment_succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/invoice.paid'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/customer.subscription.updated.2'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/payment_intent.succeeded'))
        StripeWebhookService.process_event(e('ultimate_yearly_failed_payment_then_changed_subscription/customer.subscription.created.2'))

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertFalse(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertTrue(PremiumService.is_premium_2020(valid_subscription))
        self.assertFalse(valid_subscription.cancelled)
