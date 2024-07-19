from enum import Enum


class MarketplaceLineItemShippingCostType(Enum):
    NO_SHIPPING = "NO_SHIPPING"
    COVERED_BY_SELLER = "COVERED_BY_SELLER"
    FIXED = "FIXED"
    TO_BE_AGREED = "TO_BE_AGREED"
