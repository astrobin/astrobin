from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from subscription.models import Subscription, Transaction
from subscription.utils import extend_date_by

from astrobin.tests.generators import Generators
from astrobin_apps_payments.services.stripe_webhook_service import StripeWebhookService
from astrobin_apps_payments.tests.stripe_generators import StripeGenerators
from astrobin_apps_premium.services.premium_service import PremiumService, SubscriptionName


class StripeWebhookServiceLiteMonthlyTest(TestCase):
    def setUp(self):
        self.subscription, created = Subscription.objects.get_or_create(
            name=SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY.value,
            currency="CHF",
            price=20,
            trial_period=0,
            trial_unit=None,
            recurrence_period=1,
            recurrence_unit='M',
            group=Group.objects.get_or_create(name='astrobin_ultimate_2020')[0],
            category='ultimate_autorenew'
        )

    def test_first_order(self):
        user = Generators.user(email="astrobin@astrobin.com")
        e = StripeGenerators.event

        StripeWebhookService.process_event(e('ultimate_monthly_first_order/charge.succeeded'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/payment_method.attached'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/customer.created'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/customer.updated'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/invoice.created'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/customer.subscription.created'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/invoice.finalized'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/invoice.updated'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/invoice.paid'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/invoice.payment_succeeded'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/customer.subscription.updated'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/payment_intent.succeeded'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/payment_intent.created'))
        StripeWebhookService.process_event(e('ultimate_monthly_first_order/checkout.session.completed'))

        user.userprofile.refresh_from_db()

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.expires, extend_date_by(date.today(), 1, 'M'))
        self.assertEqual(valid_subscription.subscription, self.subscription)
        self.assertIsNotNone(user.userprofile.stripe_customer_id)
        self.assertIsNotNone(user.userprofile.stripe_subscription_id)
        self.assertEqual(
            1,
            Transaction.objects.filter(
                user=user,
                subscription=self.subscription,
                event='subscription payment',
                amount=7.50,
            ).count()
        )

    def test_cancellation(self):
        user = Generators.user(email="astrobin@astrobin.com")
        user.userprofile.stripe_customer_id = 'STRIPE_CUSTOMER_ID'
        user.userprofile.save()

        e = StripeGenerators.event

        user_subscription = Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY)

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))
        self.assertEqual(valid_subscription.subscription, self.subscription)

        StripeWebhookService.process_event(e('ultimate_monthly_cancellation/billing_portal.session.created'))
        StripeWebhookService.process_event(e('ultimate_monthly_cancellation/customer.subscription.updated'))

        valid_subscription = PremiumService(user).get_valid_usersubscription()
        self.assertTrue(PremiumService.is_ultimate_2020(valid_subscription))

        user_subscription.refresh_from_db()
        self.assertTrue(user_subscription.cancelled)
