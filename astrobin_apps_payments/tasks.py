import json
import logging
from datetime import datetime

import requests
from celery import shared_task
from django.conf import settings

from astrobin_apps_payments.models import ExchangeRate

log = logging.getLogger(__name__)


@shared_task(time_limit=60, acks_late=True)
def fetch_exchange_rates():
    source = 'CHF'
    api_url = 'https://api.transferwise.com/v1/rates?source=%s&target=%s'
    headers = {'Authorization': 'Bearer %s' % settings.TRANSFERWISE_API_TOKEN}

    for target in [x for x in settings.SUPPORTED_CURRENCIES if x != source]:
        try:
            response = requests.get(api_url % (source, target), headers=headers)
            if response.status_code == 200:
                data = json.loads(response.text)[0]
                ExchangeRate.objects.create(
                    rate=data.get('rate'),
                    source=source,
                    target=target,
                    time=datetime.now(),
                )
            else:
                log.error("fetch_exchange_rates: response %d: %s" % (response.status_code, response.text))
        except Exception as e:
            log.exception("fetch_exchange_rates exception: %s", str(e))

@shared_task(time_limit=60, acks_late=True)
def process_stripe_webhook_event(event):
    from astrobin_apps_payments.services.stripe_webhook_service import StripeWebhookService

    try:
        event_type = event['type']

        log.info("process_stripe_webhook_event: %s" % event_type)

        if event_type == 'customer.created':
            StripeWebhookService.on_customer_created(event)
        elif event_type == 'customer.updated':
            StripeWebhookService.on_customer_updated(event)
        elif event_type == 'customer.deleted':
            StripeWebhookService.on_customer_deleted(event)
        elif event_type == 'payment_intent.created':
            StripeWebhookService.on_payment_intent_created(event)
        elif event_type == 'invoice.paid':
            StripeWebhookService.on_invoice_paid(event)
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
        raise e
