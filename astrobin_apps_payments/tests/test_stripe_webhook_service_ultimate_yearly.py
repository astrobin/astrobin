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


class StripeWebhookServiceLiteYearlyTest(TestCase):
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
        self.assertEqual(valid_subscription.expires, extend_date_by(date.today(), 1, 'Y'))
        self.assertEqual(valid_subscription.subscription, self.subscription)
        self.assertIsNotNone(user.userprofile.stripe_customer_id)
        self.assertIsNotNone(user.userprofile.stripe_subscription_id)
        self.assertEqual(
            1,
            Transaction.objects.filter(
                user=user,
                subscription=self.subscription,
                event='subscription payment',
                amount=self.subscription.price,
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
