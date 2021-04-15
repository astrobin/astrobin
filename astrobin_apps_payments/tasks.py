import json
import logging
from datetime import datetime

import requests
from celery import shared_task
from django.conf import settings

from astrobin_apps_payments.models import ExchangeRate

log = logging.getLogger("apps")


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
