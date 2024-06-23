import json
import re
from datetime import datetime, timedelta

import stripe
from dateutil.relativedelta import relativedelta
from django.conf import settings


class StripeGenerators(object):
    @staticmethod
    def event(filename):
        stripe.api_key = settings.STRIPE['keys']['secret']
        file_path = f'astrobin_apps_payments/tests/data/{filename}.json'

        with open(file_path) as json_file:
            file_content = json_file.read()

            def replace_placeholder(match):
                placeholder = match.group(0)  # The matched text (e.g., STRIPE_API_KEY)

                if placeholder.startswith('STRIPE_PRICE_'):
                    parts = placeholder.split('_')
                    product = parts[2].lower()
                    recurrence = parts[3].lower()
                    tier = parts[5]

                    replacement = settings.STRIPE['prices'][product][f'{recurrence}-tier-{tier}']
                elif placeholder.startswith('STRIPE_PRODUCT_'):
                    product = placeholder.split('_')[2].lower()
                    replacement = settings.STRIPE['products'][product]
                else:
                    replacement = getattr(
                        settings, placeholder, placeholder
                    )  # Get the attribute from settings or use the placeholder if not found

                return replacement

            # Replace all occurrences of STRIPE_EVENT_START_TIMESTAMP
            now = datetime.now()
            now_unix_timestamp = int(now.timestamp())
            file_content = re.sub(r'STRIPE_EVENT_START_TIMESTAMP', str(now_unix_timestamp), file_content)

            # Replace all occurrences of STRIPE_EVENT_END_TIMESTAMP
            if 'monthly' in filename:
                end = now + relativedelta(months=1)
            elif 'yearly' in filename or 'once' in filename:
                end = now + relativedelta(years=1)

            end_unix_timestamp = int(end.timestamp())
            file_content = re.sub(r'STRIPE_EVENT_END_TIMESTAMP', str(end_unix_timestamp), file_content)

            # Replace all occurrences of STRIPE_*
            file_content = re.sub(r'STRIPE_\w+', replace_placeholder, file_content)

            # Load the JSON data from the modified string
            event_data = json.loads(file_content)

            return stripe.Event.construct_from(event_data, stripe.api_key)
