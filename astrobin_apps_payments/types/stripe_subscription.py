from astrobin_apps_premium.services.premium_service import SubscriptionDisplayName, SubscriptionName


class StripeSubscription(object):
    name: SubscriptionName
    display_name: SubscriptionDisplayName

    def __init__(
            self,
            name: SubscriptionName,
            display_name: SubscriptionDisplayName,
    ):
        self.name = name
        self.display_name = display_name
