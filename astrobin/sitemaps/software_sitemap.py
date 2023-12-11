from astrobin.sitemaps.equipment_item_sitemap import EquipmentItemSitemap
from astrobin_apps_equipment.models import Software


class SoftwareSitemap(EquipmentItemSitemap):
    def __init__(self):
        super().__init__(Software)
