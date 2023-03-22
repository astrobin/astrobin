from typing import Optional


class StripeSubscription(object):
    name: str
    product_id: str
    yearly_price_id: str
    monthly_price_id: Optional[str]

    def __init__(self, name: str, product_id: str, yearly_price_id: str, monthly_price_id: Optional[str]):
        self.name = name
        self.product_id = product_id
        self.yearly_price_id = yearly_price_id
        self.monthly_price_id = monthly_price_id
