from enum import Enum


class MarketplaceListingCondition(Enum):
    UNOPENED = 'UNOPENED'
    NEW = 'NEW'
    USED = 'USED'
    DAMAGED_OR_DEFECTIVE = 'DAMAGED_OR_DEFECTIVE'
    OTHER = 'OTHER'
