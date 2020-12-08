# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from paypal.standard.ipn.models import PayPalIPN
from subscription.models import Subscription, handle_payment_was_successful

from common.services import AppRedirectionService

log = logging.getLogger("apps")


@require_GET
def stripe_config(request):
    return JsonResponse({'publicKey': settings.STRIPE_PUBLISHABLE_KEY}, safe=False)


@csrf_exempt
@require_POST
def create_checkout_session(request, user_pk, product, currency):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        log.error("create_checkout_session: %d, %s, %s: %s" % (user_pk, product, currency, "Invalid user"))
        raise Http404

    if currency.upper() not in settings.SUPPORTED_CURRENCIES:
        log.error("create_checkout_session: %d, %s, %s: %s" % (user.pk, product, currency, "Invalid currency"))
        return HttpResponseBadRequest()

    if product == 'lite':
        price = settings.STRIPE_PRICE_LITE[currency.upper()]
    elif product == 'premium':
        price = settings.STRIPE_PRICE_PREMIUM[currency.upper()]
    elif product == 'ultimate':
        price = settings.STRIPE_PRICE_ULTIMATE[currency.upper()]
    else:
        log.error("create_checkout_session: %d, %s, %s: %s" % (user.pk, product, currency, "Invalid product"))
        return HttpResponseBadRequest()

    log.info("create_checkout_session: %d, %s, %s, %s" % (user.pk, product, price, currency))

    try:
        customer_result = stripe.Customer.list(email=user.email, limit=1)
        customer = None
        if len(customer_result['data']) == 1:
            customer = customer_result['data'][0]['id']

        checkout_session = stripe.checkout.Session.create(
            success_url=AppRedirectionService.redirect(
                request,
                '/subscriptions/success?product=' + product + '&session_id={CHECKOUT_SESSION_ID}'),
            cancel_url=AppRedirectionService.redirect(request, '/subscriptions/cancelled/'),
            mode='payment',
            payment_method_types=['card'],
            client_reference_id=user.pk,
            customer=customer if customer else None,
            customer_email=user.email if not customer else None,
            allow_promotion_codes=True,
            submit_type='pay',
            line_items=[
                {
                    'price': price,
                    'quantity': 1,
                }
            ],
            metadata={
                'product': product
            }
        )
        return JsonResponse({'sessionId': checkout_session['id']})
    except Exception as e:
        log.exception("create_checkout_session: %d, %s, %s: %s" % (user.pk, product, currency, str(e)))
        return JsonResponse({'error': 'Internal error: %s' % str(e)})


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        log.exception("stripe_webhook: %s" % str(e))
        return HttpResponseBadRequest()

    log.info("stripe_webhook: %s" % event['type'])

    if event['type'] == 'checkout.session.completed':
        try:
            user_pk = int(event['data']['object']['client_reference_id'])
            product = event['data']['object']['metadata']['product']

            log.info("stripe_webhook: user %d product %s" % (user_pk, product))

            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                log.exception("stripe_webhook: user %d invalid user" % user_pk)
                return HttpResponseBadRequest()

            subscription = None

            if product == 'lite':
                subscription = Subscription.objects.get(name="AstroBin Lite 2020+")
            elif product == 'premium':
                subscription = Subscription.objects.get(name="AstroBin Premium 2020+")
            elif product == 'ultimate':
                subscription = Subscription.objects.get(name="AstroBin Ultimate 2020+")
            else:
                log.exception("stripe_webhook: user %d invalid product" % user_pk)
                return HttpResponseBadRequest()

            payment = PayPalIPN.objects.create(
                custom=user_pk,
                item_number=subscription.pk,
                mc_gross=subscription.price,
                mc_currency=subscription.currency
            )

            handle_payment_was_successful(payment)

        except KeyError as e:
            log.exception("stripe_webhook: %s" % str(e))
            return HttpResponseBadRequest()

    return HttpResponse(status=200)
