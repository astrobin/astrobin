from enum import Enum


class MarketplaceListingCondition(Enum):
    UNOPENED = 'UNOPENED'
    NEW = 'NEW'
    USER = 'USED'
    DAMAGED_OR_DEFECTIVE = 'DAMAGED_OR_DEFECTIVE'
    OTHER = 'OTHER'
