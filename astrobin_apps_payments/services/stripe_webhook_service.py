import json
import logging
import time
from datetime import datetime

import stripe
from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.http import HttpResponseBadRequest
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.models import ST_PP_CANCELLED, ST_PP_COMPLETED, ST_PP_CREATED, ST_PP_PAID
from stripe.error import StripeError
from subscription.models import (
    Subscription, Transaction, UserSubscription, handle_payment_was_successful,
    handle_subscription_cancel, handle_subscription_signup,
)
from subscription.signals import paid

from astrobin.models import UserProfile
from astrobin_apps_notifications.services.notifications_service import NotificationContext
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_payments.tasks import process_stripe_webhook_event
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
                    raise AttributeError("Unable to fetch customer")

                if hasattr(customer, 'deleted') and customer.deleted:
                    log.error("stripe_webhook: customer id %s has been deleted" % customer_id)
                    raise AttributeError("Customer has been deleted")
                if not hasattr(customer, 'email'):
                    log.error("stripe_webhook: customer id %s has no email" % customer_id)
                    raise AttributeError("Customer has no email")
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
                raise AttributeError("User not found")

        return user

    @staticmethod
    def get_subscription_from_product_id(product_id: str, recurring_unit: str) -> Subscription:
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
    def get_subscription_from_session(session) -> Subscription:
        product_id = session['items']['data'][0]['price']['product']
        recurring_unit = session['items']['data'][0]['price']['recurring']['interval']
        return StripeWebhookService.get_subscription_from_product_id(product_id, recurring_unit)

    @staticmethod
    def get_overdue_subscriptions(customer_id):
        stripe.api_key = settings.STRIPE['keys']['secret']
        subscriptions = stripe.Subscription.list(customer=customer_id)
        return [sub for sub in subscriptions.auto_paging_iter() if sub.status == 'past_due']

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
        UserProfile.objects.filter(stripe_customer_id=session['id']).update(
            stripe_customer_id=None,
            stripe_subscription_id=None
        )

    @staticmethod
    def on_payment_intent_created(event):
        session = StripeWebhookService.get_session_from_event(event)

        # We take the chance here to make sure the user has a stripe customer id.
        if 'recipient_email' in session:
            UserProfile.objects\
                .filter(user__email=session['recipient_email'])\
                .update(stripe_customer_id=session['customer'])

    @staticmethod
    def on_invoice_paid(event):
        session = StripeWebhookService.get_session_from_event(event)
        user = StripeWebhookService.get_user_from_session(session)

        for line in session['lines']['data']:
            product_id = line['price']['product']
            recurring_unit = line['price']['recurring']['interval']
            subscription = StripeWebhookService.get_subscription_from_product_id(product_id, recurring_unit)
            user_subscription: UserSubscription = get_object_or_None(
                UserSubscription, user=user, subscription=subscription
            )

            amount = line['amount'] / 100

            if 'discount_amounts' in line:
                for discount_amount in line['discount_amounts']:
                    amount -= discount_amount['amount'] / 100

            ipn = PayPalIPN.objects.create(
                custom=user.pk,
                item_number=subscription.pk,
                payment_status=ST_PP_PAID,
                mc_gross=amount
            )

            Transaction(
                user=user,
                subscription=subscription,
                ipn=ipn,
                event='subscription payment',
                amount=amount,
                comment=session['hosted_invoice_url']
            ).save()

            paid.send(
                subscription,
                ipn=ipn,
                subscription=subscription,
                user=user,
                usersubscription=user_subscription,
            )

        if session['amount_paid'] > 0:
            push_notification(
                [user],
                None,
                'new_payment',
                {
                    'BASE_URL': settings.BASE_URL,
                    'extra_tags': {
                        'context': NotificationContext.SUBSCRIPTIONS
                    },
                }
            )
        else:
            log.debug("stripe_webhook: invoice paid with amount less than 0 by user %s" % user.pk)

    @staticmethod
    def on_customer_subscription_deleted(event):
        session = StripeWebhookService.get_session_from_event(event)
        user = StripeWebhookService.get_user_from_session(session)
        subscription = StripeWebhookService.get_subscription_from_session(session)
        user_subscription: UserSubscription = get_object_or_None(
            UserSubscription, user=user, subscription=subscription
        )

        if user.userprofile.stripe_subscription_id and user.userprofile.stripe_subscription_id != session['id']:
            log.info(
                "stripe_webhook: user %s subscription id %s does not match session id %s" % (
                    user.pk, user.userprofile.stripe_subscription_id, session['id']
                )
            )
            return

        if user_subscription:
            user_subscription.delete()

        UserProfile.objects \
            .filter(stripe_subscription_id=session['id']) \
            .update(stripe_subscription_id=None, updated=timezone.now())

    @staticmethod
    def on_customer_subscription_updated(event):
        session = StripeWebhookService.get_session_from_event(event)
        user = StripeWebhookService.get_user_from_session(session)
        subscription = StripeWebhookService.get_subscription_from_session(session)
        user_subscription: UserSubscription = get_object_or_None(
            UserSubscription, user=user, subscription=subscription
        )

        if user_subscription is None:
            user_subscription = UserSubscription.objects.create(
                user=user,
                subscription=subscription,
                active=session['status'] == 'active',
                expires=datetime.fromtimestamp(session['current_period_end']).date(),
                cancelled=session['cancel_at_period_end'],
            )

            log.debug(
                f"on_customer_subscription_updated: Subscription for user {user.pk}, {subscription.name}, created: "
                f"active={user_subscription.active}, cancelled={user_subscription.cancelled}"
            )
        else:
            if user.userprofile.stripe_subscription_id and user.userprofile.stripe_subscription_id != session['id']:
                log.info(
                    "stripe_webhook: user %s subscription id %s does not match session id %s" % (
                        user.pk, user.userprofile.stripe_subscription_id, session['id']
                    )
                )
                return

        user_subscription.expires = datetime.fromtimestamp(session['current_period_end']).date()
        user_subscription.active = session['status'] == 'active'
        user_subscription.cancelled = session['cancel_at_period_end'] if user_subscription.active else True
        user_subscription.save()

        log.debug(
            f"on_customer_subscription_updated: Subscription for user {user.pk}, {subscription.name}, saved: "
            f"active={user_subscription.active}, cancelled={user_subscription.cancelled}"
        )

        UserProfile.all_objects.filter(user=user).update(updated=timezone.now())

        if 'previous_attributes' in event['data']:
            if user_subscription and 'cancel_at_period_end' in event['data']['previous_attributes']:
                if user_subscription.cancelled:
                    ipn = PayPalIPN.objects.create(
                        custom=user.pk,
                        item_number=subscription.pk,
                        payment_status=ST_PP_CANCELLED,
                    )

                    handle_subscription_cancel(ipn)

            if user_subscription and 'status' in event['data']['previous_attributes']:
                if user_subscription.active:
                    push_notification(
                        [user],
                        None,
                        'new_subscription',
                        {
                            'BASE_URL': settings.BASE_URL,
                            'subscription': subscription,
                            'extra_tags': {
                                'context': NotificationContext.SUBSCRIPTIONS
                            },
                        }
                    )

            if 'items' in event['data']['previous_attributes']:
                new_attributes = session['items']['data'][0]
                previous_attributes = event['data']['previous_attributes']['items']['data'][0]
                if previous_attributes['price']['product'] != new_attributes['price']['product']:
                    previous_subscription = StripeWebhookService.get_subscription_from_session(
                        event['data']['previous_attributes']
                    )
                    previous_user_subscription: UserSubscription = get_object_or_None(
                        UserSubscription, user=user, subscription=previous_subscription
                    )

                    if previous_user_subscription:
                        previous_user_subscription.delete()
                    else:
                        log.error(f"Unexpected user subscription change for {user.pk}")

    @staticmethod
    def on_customer_subscription_created(event):
        session = StripeWebhookService.get_session_from_event(event)
        user = StripeWebhookService.get_user_from_session(session)
        subscription = StripeWebhookService.get_subscription_from_session(session)
        incomplete = session['status'] == 'incomplete'

        UserProfile.objects \
            .filter(user=user) \
            .update(stripe_subscription_id=session['id'])

        try:
            # If the user already has a subscription, we don't need to do anything.
            user_subscription = UserSubscription.objects.get(user=user, subscription=subscription)
            log.debug(
                f"on_customer_subscription_created: User {user.pk} already has a subscription for {subscription.name}: "
                f"active={user_subscription.active}, cancelled={user_subscription.cancelled}"
            )
        except UserSubscription.DoesNotExist:
            ipn = PayPalIPN.objects.create(
                custom=user.pk,
                item_number=subscription.pk,
                mc_gross=subscription.price,
                mc_currency=subscription.currency,
                payment_status=ST_PP_CREATED,
            )

            try:
                handle_subscription_signup(ipn)
            except IntegrityError as e:
                pass

            user_subscription = UserSubscription.objects.get(user=user, subscription=subscription)
            user_subscription.active = not incomplete
            user_subscription.cancelled = session['cancel_at_period_end'] if user_subscription.active else True

        user_subscription.expires = datetime.fromtimestamp(session['current_period_end']).date()
        user_subscription.save()

        try:
            overdue_subscriptions = StripeWebhookService.get_overdue_subscriptions(session['customer'])
            for overdue_subscription in overdue_subscriptions:
                stripe.api_key = settings.STRIPE['keys']['secret']
                stripe.Subscription.modify(overdue_subscription.id, pause_collection={'behavior': 'mark_uncollectible'})
                stripe.Subscription.cancel(overdue_subscription.id)

                if hasattr(overdue_subscription, 'latest_invoice') and overdue_subscription.latest_invoice:
                    stripe.Invoice.void_invoice(overdue_subscription.latest_invoice)
                    stripe.Invoice.mark_uncollectible(overdue_subscription.latest_invoice)
        except StripeError as e:
            log.exception(f"stripe_webhook: unable to cancel overdue subscriptions for {session['customer']}: {str(e)}")
        except Exception as e:
            log.exception(
                f"stripe_webhook: unexpected error while trying to cancel overdue subscriptions for "
                f"{session['customer']}: {str(e)}"
            )

        log.debug(
            f"on_customer_subscription_created: Subscription for user {user.pk}, {subscription.name}, saved: "
            f"active={user_subscription.active}, cancelled={user_subscription.cancelled}"
        )

        if user_subscription.active:
            push_notification(
                [user],
                None,
                'new_subscription',
                {
                    'BASE_URL': settings.BASE_URL,
                    'subscription': subscription,
                    'extra_tags': {
                        'context': NotificationContext.SUBSCRIPTIONS
                    },
                }
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
            User.objects.get(pk=user_pk)
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
        # As Stripe events can come in random order, we force some delays here to attempt to keep some sanity.
        # This is not a perfect solution, but it's better than nothing.

        delay_map = {
            "customer.subscription.updated": 5,
        }

        event_type = event['type']

        try:
            delay = delay_map[event_type]
        except KeyError:
            delay = 0

        if hasattr(settings, 'CELERY_TASK_ALWAYS_EAGER') and settings.CELERY_TASK_ALWAYS_EAGER and delay > 0:
            # We need this delay also during testing and development.
            log.debug(f"process_event: delaying task {event_type} {delay} seconds")
            time.sleep(delay)

        process_stripe_webhook_event.apply_async(args=(event,), countdown=delay)
