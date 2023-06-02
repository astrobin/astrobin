import json

import stripe
from django.conf import settings


class StripeGenerators(object):
    @staticmethod
    def event(filename):
        stripe.api_key = settings.STRIPE['keys']['secret']
        file_path = f'astrobin_apps_payments/tests/data/{filename}.json'
        with open(file_path) as json_file:
            event_data = json.load(json_file)
            return stripe.Event.construct_from(event_data, stripe.api_key)
