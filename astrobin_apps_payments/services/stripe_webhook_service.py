import json
import logging
from datetime import datetime

import stripe
from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseBadRequest
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.models import ST_PP_CANCELLED, ST_PP_COMPLETED, ST_PP_CREATED
from stripe.error import StripeError
from subscription.models import (
    Subscription, Transaction, UserSubscription, handle_payment_was_successful,
    handle_subscription_cancel, handle_subscription_signup,
)
from subscription.signals import paid

from astrobin.models import UserProfile
from astrobin_apps_premium.services.premium_service import SubscriptionName

log = logging.getLogger(__name__)


class StripeWebhookService(object):
    @staticmethod
    def get_session_from_event(event):
        return event['data']['object']

    @staticmethod
    def get_user_from_session(session) -> User:
        customer_id = session['customer']

        user = get_object_or_None(User, userprofile__stripe_customer_id=customer_id)

        if user is None:
            try:
                user = User.objects.get(email=session['customer_email'])
            except KeyError:
                stripe.api_key = settings.STRIPE['keys']['secret']
                try:
                    customer = stripe.Customer.retrieve(customer_id)
                except StripeError:
                    log.exception("stripe_webhook: unable to fetch customer id %s" % customer_id)
                    raise
                user = get_object_or_None(User, email=customer.email)
                if user is None:
                    log.exception(
                        "stripe_webhook: user invalid user by customer id %s and email %s" % (
                            customer_id,
                            customer.email
                        )
                    )
                    raise AttributeError("User not found")
            except User.DoesNotExist:
                log.exception("stripe_webhook: user invalid user by customer id %s" % customer_id)
                raise

        return user

    @staticmethod
    def get_subscription_from_session(session) -> Subscription:
        product_id = session['items']['data'][0]['price']['product']
        recurring_unit = session['items']['data'][0]['price']['recurring']['interval']

        subscription_map = {
            settings.STRIPE['products']['lite']:
                SubscriptionName.LITE_2020_AUTORENEW_MONTHLY if recurring_unit == 'month'
                else SubscriptionName.LITE_2020_AUTORENEW_YEARLY,
            settings.STRIPE['products']['premium']:
                SubscriptionName.PREMIUM_2020_AUTORENEW_MONTHLY if recurring_unit == 'month'
                else SubscriptionName.PREMIUM_2020_AUTORENEW_YEARLY,
            settings.STRIPE['products']['ultimate']:
                SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY if recurring_unit == 'month'
                else SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY,
        }

        subscription_name = subscription_map[product_id]
        subscription = Subscription.objects.get(name=subscription_name.value)

        return subscription

    @staticmethod
    def on_customer_created(event):
        session = StripeWebhookService.get_session_from_event(event)
        UserProfile.objects.filter(user__email=session['email']).update(stripe_customer_id=session['id'])

    @staticmethod
    def on_customer_updated(event):
        session = StripeWebhookService.get_session_from_event(event)
        UserProfile.objects.filter(user__email=session['email']).update(stripe_customer_id=session['id'])

    @staticmethod
    def on_customer_deleted(event):
        session = StripeWebhookService.get_session_from_event(event)
        UserProfile.objects.filter(stripe_customer_id=session['id']).update(stripe_customer_id=None)

    @staticmethod
    def on_payment_intent_created(event):
        session = StripeWebhookService.get_session_from_event(event)

        # We take the chance here to make sure the user has a stripe customer id.
        if 'recipient_email' in session:
            UserProfile.objects\
                .filter(user__email=session['recipient_email'])\
                .update(stripe_customer_id=session['customer'])

    @staticmethod
    def on_customer_subscription_deleted(event):
        session = StripeWebhookService.get_session_from_event(event)
        user = StripeWebhookService.get_user_from_session(session)
        subscription = StripeWebhookService.get_subscription_from_session(session)

        UserProfile.objects \
            .filter(user=user) \
            .update(stripe_subscription_id=None, updated=timezone.now())

        ipn = PayPalIPN.objects.create(
            custom=user.pk,
            item_number=subscription.pk,
            payment_status=ST_PP_CANCELLED,
        )

        handle_subscription_cancel(ipn)

    @staticmethod
    def on_customer_subscription_updated(event):
        session = StripeWebhookService.get_session_from_event(event)
        user = StripeWebhookService.get_user_from_session(session)
        subscription = StripeWebhookService.get_subscription_from_session(session)
        user_subscription: UserSubscription = get_object_or_None(
            UserSubscription, user=user, subscription=subscription
        )

        UserProfile.all_objects.filter(user=user).update(updated=timezone.now())

        if 'previous_attributes' in event['data']:
            if 'cancel_at_period_end' in event['data']['previous_attributes']:
                user_subscription.cancelled = session['cancel_at_period_end']
                user_subscription.save()
            elif 'current_period_end' in event['data']['previous_attributes']:
                user_subscription.expires = datetime.fromtimestamp(session['current_period_end']).date()
                user_subscription.save()
            elif 'items' in event['data']['previous_attributes']:
                new_attributes = session['items']['data'][0]
                previous_attributes = event['data']['previous_attributes']['items']['data'][0]
                if previous_attributes['price']['product'] != new_attributes['price']['product']:
                    previous_subscription = StripeWebhookService.get_subscription_from_session(
                        event['data']['previous_attributes']
                    )
                    previous_user_subscription: UserSubscription = get_object_or_None(
                        UserSubscription, user=user, subscription=previous_subscription
                    )

                    previous_user_subscription.subscription = subscription
                    previous_user_subscription.save()

    @staticmethod
    def on_customer_subscription_created(event):
        session = StripeWebhookService.get_session_from_event(event)
        user = StripeWebhookService.get_user_from_session(session)
        subscription = StripeWebhookService.get_subscription_from_session(session)

        UserProfile.objects \
            .filter(user=user) \
            .update(stripe_subscription_id=session['id'])

        ipn = PayPalIPN.objects.create(
            custom=user.pk,
            item_number=subscription.pk,
            mc_gross=subscription.price,
            mc_currency=subscription.currency,
            payment_status=ST_PP_CREATED,
        )

        handle_subscription_signup(ipn)

        user_subscription = UserSubscription.objects.get(user=user, subscription=subscription)
        user_subscription.extend()
        user_subscription.save()

        Transaction(
            user=user,
            subscription=subscription,
            ipn=ipn,
            event='subscription payment',
            amount=ipn.mc_gross,
        ).save()

        paid.send(
            subscription,
            ipn=ipn,
            subscription=subscription,
            user=user,
            usersubscription=user_subscription,
        )

    @staticmethod
    def on_checkout_session_completed(event):
        session = StripeWebhookService.get_session_from_event(event)
        product = session['metadata']['product']

        try:
            recurring_unit = session['metadata']['recurring-unit']
        except KeyError:
            recurring_unit = 'once'

        autorenew = recurring_unit != 'once'

        if autorenew:
            # We don't handle autorenew subscriptions here, only one-time payments.
            return

        user_pk = int(session['client_reference_id'])

        log.info("stripe_webhook: user %d product %s / %s / %s" % (user_pk, product, recurring_unit, autorenew))

        try:
            user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            log.exception("stripe_webhook: user %d invalid user" % user_pk)
            return HttpResponseBadRequest()

        subscription_map = {
            'lite-once': SubscriptionName.LITE_2020,
            'premium-once': SubscriptionName.PREMIUM_2020,
            'ultimate-once': SubscriptionName.ULTIMATE_2020,
        }

        subscription_key = product + '-' + recurring_unit
        subscription = Subscription.objects.get(name=subscription_map[subscription_key].value)

        ipn = PayPalIPN.objects.create(
            custom=user_pk,
            item_number=subscription.pk,
            mc_gross=subscription.price,
            mc_currency=subscription.currency,
            payment_status=ST_PP_COMPLETED,
        )

        handle_payment_was_successful(ipn)

    @staticmethod
    def on_checkout_session_async_payment_succeeded(event):
        log.info("stripe_webhook: payment succeeded for event %s" % event['id'])

    @staticmethod
    def on_checkout_session_async_payment_failed(event):
        log.info("stripe_webhook: payment failed for event %s" % event['id'])
        msg = EmailMultiAlternatives(
            '[AstroBin] User payment failed',
            'Payment from user failed: <br/>%s' % json.dumps(event, indent=4, sort_keys=True),
            settings.DEFAULT_FROM_EMAIL,
            ['astrobin@astrobin.com']
        )
        msg.send()

    @staticmethod
    def process_event(event):
        try:
            event_type = event['type']

            if event_type == 'customer.created':
                StripeWebhookService.on_customer_created(event)
            elif event_type == 'customer.updated':
                StripeWebhookService.on_customer_updated(event)
            elif event_type == 'customer.deleted':
                StripeWebhookService.on_customer_deleted(event)
            elif event_type == 'payment_intent.created':
                StripeWebhookService.on_payment_intent_created(event)
            elif event_type == 'customer.subscription.created':
                StripeWebhookService.on_customer_subscription_created(event)
            elif event_type == 'customer.subscription.deleted':
                StripeWebhookService.on_customer_subscription_deleted(event)
            elif event_type == 'customer.subscription.updated':
                StripeWebhookService.on_customer_subscription_updated(event)
            elif event_type == 'checkout.session.completed':
                StripeWebhookService.on_checkout_session_completed(event)
            elif event_type == 'checkout.session.async_payment_succeeded':
                StripeWebhookService.on_checkout_session_async_payment_succeeded(event)
            elif event_type == 'checkout.session.async_payment_failed':
                StripeWebhookService.on_checkout_session_async_payment_failed(event)
            else:
                log.info("stripe_webhook: unhandled event %s" % event_type)
        except Exception as e:
            log.exception("stripe_webhook: %s" % str(e))
            return HttpResponseBadRequest()
