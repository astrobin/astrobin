from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.types import StockStatus


class StockInterface:
    pk: int  # AstroBin ID
    klass: EquipmentItemKlass
    name: str
    sku: str
    url: str
    stock_status: StockStatus
    stock_amount: int

    def __init__(
            self,
            pk: int,
            klass: EquipmentItemKlass,
            name: str,
            sku: str,
            url: str,
            stock_status: StockStatus,
            stock_amount: int
    ):
        self.pk = pk
        self.klass = klass
        self.name = name
        self.sku = sku
        self.url = url
        self.stock_status = stock_status
        self.stock_amount = stock_amount

    def __str__(self):
        return f'{self.klass} {self.pk}: SKU {self.sku}, {self.name}, {self.url},' \
               f' stock status: {self.stock_status.value}, ' \
               f'stock amount: {self.stock_amount}'
