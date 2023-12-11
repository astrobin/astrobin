from astrobin.sitemaps.equipment_item_sitemap import EquipmentItemSitemap
from astrobin_apps_equipment.models import Accessory


class AccessorySitemap(EquipmentItemSitemap):
    def __init__(self):
        super().__init__(Accessory)
