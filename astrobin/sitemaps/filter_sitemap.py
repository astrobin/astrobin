from astrobin.sitemaps.equipment_item_sitemap import EquipmentItemSitemap
from astrobin_apps_equipment.models import Filter


class FilterSitemap(EquipmentItemSitemap):
    def __init__(self):
        super().__init__(Filter)
