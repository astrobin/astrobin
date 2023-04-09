from typing import Optional

from astrobin_apps_premium.services.premium_service import SubscriptionDisplayName, SubscriptionName


class StripeSubscription(object):
    name: SubscriptionName
    display_name: SubscriptionDisplayName
    product_id: str
    yearly_price_id: str
    monthly_price_id: Optional[str]

    def __init__(
            self,
            name: SubscriptionName,
            display_name: SubscriptionDisplayName,
            product_id: str,
            yearly_price_id: str,
            monthly_price_id: Optional[str]
    ):
        self.name = name
        self.display_name = display_name
        self.product_id = product_id
        self.yearly_price_id = yearly_price_id
        self.monthly_price_id = monthly_price_id
