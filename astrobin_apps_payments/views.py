# -*- coding: utf-8 -*-

import logging

import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.utils.translation import gettext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from astrobin.models import Image
from astrobin.utils import get_client_country_code
from astrobin_apps_payments.services.pricing_service import PricingService
from astrobin_apps_payments.services.stripe_webhook_service import StripeWebhookService
from astrobin_apps_payments.types import SubscriptionRecurringUnit
from astrobin_apps_premium.services.premium_service import SubscriptionDisplayName
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

    country_code = user.userprofile.signup_country or get_client_country_code(request) or 'us'
    country_code = country_code.lower() if country_code != 'UNKNOWN' else 'us'

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

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        log.exception("stripe_webhook: %s" % str(e))
        return HttpResponseBadRequest()

    log.info("stripe_webhook: %s" % event['type'])

    StripeWebhookService.process_event(event)

    return HttpResponse(status=200)
