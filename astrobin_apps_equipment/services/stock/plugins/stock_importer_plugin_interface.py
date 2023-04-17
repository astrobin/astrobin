from typing import List, Tuple

from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.types import StockStatus
from astrobin_apps_equipment.types.stock_interface import StockInterface


class StockImporterPluginInterface:
    retailer_name: str

    def parse_astrobin_id(self, astrobin_id) -> Tuple[int, EquipmentItemKlass]:
        pass

    def parse_stock_status(self, stock_status_str) -> StockStatus:
        pass

    def fetch_data(self) -> List[StockInterface]:
        pass
