import logging

from django.core.management import BaseCommand

from astrobin_apps_equipment.services.stock import StockImporterService
from astrobin_apps_equipment.services.stock.plugins.agena import AgenaStockImporterPlugin

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Import the product stock information from Agena"

    def handle(self, *args, **kwargs):
        log.info(self.help)

        importer = StockImporterService(AgenaStockImporterPlugin())

        importer.import_stock()
