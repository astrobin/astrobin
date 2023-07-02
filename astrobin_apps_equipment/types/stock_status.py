from enum import Enum


class StockStatus(Enum):
    UNKNOWN = 'UNKNOWN'
    BACK_ORDER = 'BACK_ORDER'
    IN_STOCK = 'IN_STOCK'
    OUT_OF_STOCK = 'OUT_OF_STOCK'
