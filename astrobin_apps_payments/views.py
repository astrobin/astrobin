# -*- coding: utf-8 -*-


import json
import logging

import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils.translation import gettext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.models import ST_PP_CANCELLED, ST_PP_COMPLETED, ST_PP_CREATED
from subscription.models import (
    Subscription, handle_payment_was_successful, handle_subscription_cancel,
    handle_subscription_signup,
)

from astrobin.models import Image, UserProfile
from astrobin.utils import get_client_country_code
from astrobin_apps_payments.services.pricing_service import PricingService
from astrobin_apps_payments.types import SubscriptionRecurringUnit
from astrobin_apps_premium.services.premium_service import SubscriptionDisplayName, SubscriptionName
from common.services import AppRedirectionService

log = logging.getLogger(__name__)


def __validate_session_data(user_pk: int, product: str, currency: str, recurring_unit: str, autorenew: str):
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        log.error("__validate_session_data: %d, %s, %s: %s" % (user_pk, product, currency, "Invalid user"))
        raise Http404

    if currency.upper() not in settings.SUPPORTED_CURRENCIES:
        log.error("__validate_session_data: %d, %s, %s: %s" % (user.pk, product, currency, "Invalid currency"))
        return HttpResponseBadRequest()

    if product not in ('lite', 'premium', 'ultimate'):
        log.error("__validate_session_data: %d, %s, %s: %s" % (user.pk, product, currency, "Invalid product"))
        return HttpResponseBadRequest()

    image_count = Image.objects_including_wip.filter(user=user).count()
    if product == 'lite' and image_count >= settings.PREMIUM_MAX_IMAGES_LITE_2020:
        log.error("__validate_session_data: %d, %s, %s: %s" % (user.pk, product, currency, "Too many images for Lite"))
        return HttpResponseBadRequest(
            gettext(
                'The Lite plan is capped at %(lite_max)s total images, and you currently have %(count)s images on '
                'AstroBin.' % {
                    'lite_max': settings.PREMIUM_MAX_IMAGES_LITE_2020,
                    'count': image_count
                },
            )
        )

    if autorenew != 'true' and not PricingService.non_autorenewing_supported(user):
        log.error(
            "__validate_session_data: %d, %s, %s: %s" % (user.pk, product, currency, "Non-autorenew not supported")
        )
        return HttpResponseBadRequest(
            gettext(
                'Non-autorenewing subscriptions are not supported for your account.'
                ' Please contact us for more information.'
            )
        )

    if autorenew == 'false':
        recurring_unit = None

    return user, product, currency, recurring_unit, autorenew

@require_GET
def stripe_config(request):
    return JsonResponse({'publicKey': settings.STRIPE['keys']['publishable']}, safe=False)


@csrf_exempt
@require_POST
def create_checkout_session(request, user_pk: int, product: str, currency: str, recurring_unit: str, autorenew: str):
    stripe.api_key = settings.STRIPE['keys']['secret']

    user, product, currency, recurring_unit, autorenew = __validate_session_data(
        user_pk, product, currency, recurring_unit, autorenew
    )

    country_code = get_client_country_code(request)

    price = PricingService.get_full_price(
        SubscriptionDisplayName.from_string(product),
        country_code,
        currency.upper(),
        SubscriptionRecurringUnit.from_string(recurring_unit),
    )

    log.info(
        "create_checkout_session: %d, %s, %s, %s, %s, %s, %.2f" % (
            user.pk, product, country_code, currency, recurring_unit, autorenew, price)
    )

    try:
        customer = PricingService.get_stripe_customer(user)
        customer_id = None
        if customer:
            customer_id = customer['id']

        discounts = PricingService.get_stripe_discounts(user)

        if currency.upper() == 'EUR':
            payment_method_types = ['card', 'sepa_debit']
        elif currency.upper() == 'CNY':
            payment_method_types = ['card', 'alipay']
        else:
            payment_method_types = ['card']

        kwargs = {
            'success_url': AppRedirectionService.redirect(
                '/subscriptions/success?product=' + product + '&session_id={CHECKOUT_SESSION_ID}'
            ),
            'cancel_url': AppRedirectionService.redirect('/subscriptions/cancelled/'),
            'mode': 'subscription' if autorenew != 'false' else 'payment',
            'payment_method_types': payment_method_types,
            'client_reference_id': user.pk,
            'customer': customer_id if customer_id else None,
            'customer_email': user.email if not customer_id else None,
            'currency': currency.lower(),
            'line_items': [
                {
                    'quantity': 1,
                    'price': PricingService.get_stripe_price_object(
                        SubscriptionDisplayName.from_string(product),
                        country_code,
                        SubscriptionRecurringUnit.from_string(recurring_unit)
                    )['id']
                }
            ],
            'metadata': {
                'product': product,
                'recurring-unit': recurring_unit,
                'autorenew': autorenew,
            },
        }

        if discounts:
            kwargs['discounts'] = discounts
        else:
            kwargs['allow_promotion_codes'] = True

        checkout_session = stripe.checkout.Session.create(**kwargs)

        return JsonResponse({'sessionId': checkout_session['id']})
    except Exception as e:
        log.exception("create_checkout_session: %d, %s, %s: %s" % (user.pk, product, currency, str(e)))
        return JsonResponse({'error': 'Internal error: %s' % str(e)})


@csrf_exempt
@require_POST
def upgrade_subscription(request, user_pk: int, product: str, currency: str, recurring_unit: str):
    stripe.api_key = settings.STRIPE['keys']['secret']

    user, product, currency, recurring_unit, autorenew = __validate_session_data(
        user_pk, product, currency, recurring_unit, 'true'
    )

    country_code = get_client_country_code(request)

    price = PricingService.get_stripe_price_object(
        SubscriptionDisplayName.from_string(product),
        country_code,
        SubscriptionRecurringUnit.from_string(recurring_unit),
    )

    log.info(
        "upgrade: %d, %s, %s, %s, %s, %s, %.2f" % (
            user.pk, product, country_code, currency, recurring_unit, autorenew, price['unit_amount'])
    )

    stripe_subscription_id = user.userprofile.stripe_subscription_id
    stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)

    try:
        stripe.Subscription.modify(
            stripe_subscription.id,
            cancel_at_period_end=False,
            proration_behavior='create_prorations',
            items=[{
                'id': stripe_subscription['items']['data'][0].id,
                'price': price['id'],
            }]
        )
    except Exception as e:
        log.exception("upgrade: %d, %s, %s: %s" % (user.pk, product, currency, str(e)))
        return JsonResponse({'error': 'Internal error: %s' % str(e)})

    return JsonResponse({'subscriptionId': stripe_subscription_id})


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE['keys']['secret']
    endpoint_secret = settings.STRIPE['keys']['endpoint-secret']
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    def fulfill_cancellation(session):
        product_id = session['items']['data'][0]['price']['product']
        recurring_unit = session['items']['data'][0]['price']['recurring']['interval']
        customer_id = session['customer']

        try:
            user = User.objects.get(userprofile__stripe_customer_id=customer_id)
        except User.DoesNotExist:
            log.exception("stripe_webhook: user %d invalid user by customer id" % customer_id)
            return HttpResponseBadRequest()

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

        subscription = Subscription.objects.get(name=subscription_map[product_id].value)

        ipn = PayPalIPN.objects.create(
            custom=user.pk,
            item_number=subscription.pk,
            payment_status=ST_PP_CANCELLED,
        )

        handle_subscription_cancel(ipn)

    def fulfill_payment(session):
        product = session['metadata']['product']

        try:
            recurring_unit = session['metadata']['recurring-unit']
        except KeyError:
            recurring_unit = 'once'

        autorenew = session['metadata']['autorenew']
        user_pk = int(session['client_reference_id'])

        log.info("stripe_webhook: user %d product %s / %s / %s" % (user_pk, product, recurring_unit, autorenew))

        try:
            user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            log.exception("stripe_webhook: user %d invalid user" % user_pk)
            return HttpResponseBadRequest()

        subscription_map = {
            'lite-monthly': SubscriptionName.LITE_2020_AUTORENEW_MONTHLY,
            'lite-yearly': SubscriptionName.LITE_2020_AUTORENEW_YEARLY,
            'lite-once': SubscriptionName.LITE_2020,
            'premium-monthly': SubscriptionName.PREMIUM_2020_AUTORENEW_MONTHLY,
            'premium-yearly': SubscriptionName.PREMIUM_2020_AUTORENEW_YEARLY,
            'premium-once': SubscriptionName.PREMIUM_2020,
            'ultimate-monthly': SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY,
            'ultimate-yearly': SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY,
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

        if autorenew == 'true':
            ipn = PayPalIPN.objects.create(
                custom=user_pk,
                item_number=subscription.pk,
                mc_gross=subscription.price,
                mc_currency=subscription.currency,
                payment_status=ST_PP_CREATED,
            )

            handle_subscription_signup(ipn)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        log.exception("stripe_webhook: %s" % str(e))
        return HttpResponseBadRequest()

    log.info("stripe_webhook: %s" % event['type'])

    try:
        type = event['type']
        session = event['data']['object']

        if type == 'customer.created':
            UserProfile.objects \
                .filter(user__email=event['data']['object']['email']) \
                .update(stripe_customer_id=event['data']['object']['id'])
        elif type == 'customer.deleted':
            UserProfile.objects \
                .filter(stripe_customer_id=event['data']['object']['id']) \
                .update(stripe_customer_id=None)
        elif type == 'customer.subscription.created':
            UserProfile.objects \
                .filter(stripe_customer_id=event['data']['object']['customer']) \
                .update(stripe_subscription_id=event['data']['object']['id'])
        elif type == 'customer.subscription.deleted':
            UserProfile.objects \
                .filter(stripe_subscription_id=event['data']['object']['id']) \
                .update(stripe_subscription_id=None)
            fulfill_cancellation(session)
        elif type == 'customer.subscription.updated':
            if session['cancel_at']:
                fulfill_cancellation(session)
        elif type == 'checkout.session.completed':
            fulfill_payment(session)
        elif event['type'] == 'checkout.session.async_payment_succeeded':
            log.info("stripe_webhook: payment succeeded for event %s" % event['id'])
        elif event['type'] == 'checkout.session.async_payment_failed':
            log.info("stripe_webhook: payment failed for event %s" % event['id'])
            msg = EmailMultiAlternatives(
                '[AstroBin] User payment failed',
                'Payment from user failed: <br/>%s' % json.dumps(session, indent=4, sort_keys=True),
                settings.DEFAULT_FROM_EMAIL,
                ['astrobin@astrobin.com']
            )
            msg.send()
    except KeyError as e:
        log.exception("stripe_webhook: %s" % str(e))
        return HttpResponseBadRequest()

    return HttpResponse(status=200)
