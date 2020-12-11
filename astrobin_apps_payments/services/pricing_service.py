from math import ceil

from subscription.models import Subscription

from astrobin_apps_payments.models import ExchangeRate


class PricingService:
    @staticmethod
    def get_price(product, currency):
        # type: (unicode, unicode) -> float

        subscriptions = {
            'lite': Subscription.objects.get(name='AstroBin Lite 2020+'),
            'premium': Subscription.objects.get(name='AstroBin Premium 2020+'),
            'ultimate': Subscription.objects.get(name='AstroBin Ultimate 2020+'),
        }

        base_price = subscriptions[product].price
        exchange_rate = ExchangeRate.objects.filter(target=currency.upper()).first().rate if currency.upper() != "CHF" else 1
        exact_price = base_price * exchange_rate
        rounded_price = ceil(exact_price * 2) / 2

        return rounded_price
