import logging
from datetime import datetime
from typing import Dict

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from astrobin_apps_equipment.models import (
    Accessory, Camera, EquipmentItemListing, EquipmentRetailer, Filter, Mount,
    Software, Telescope,
)
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.services.stock.plugins import StockImporterPluginInterface

log = logging.getLogger(__name__)


class StockImporterService:
    plugin: StockImporterPluginInterface = None

    def __init__(self, plugin):
        self.plugin = plugin

    def import_stock(self):
        content_type_map: Dict[EquipmentItemKlass, ContentType] = {
            EquipmentItemKlass.TELESCOPE: ContentType.objects.get_for_model(Telescope),
            EquipmentItemKlass.CAMERA: ContentType.objects.get_for_model(Camera),
            EquipmentItemKlass.MOUNT: ContentType.objects.get_for_model(Mount),
            EquipmentItemKlass.FILTER: ContentType.objects.get_for_model(Filter),
            EquipmentItemKlass.ACCESSORY: ContentType.objects.get_for_model(Accessory),
            EquipmentItemKlass.SOFTWARE: ContentType.objects.get_for_model(Software),
        }

        data = self.plugin.fetch_data()

        if len(data) == 0:
            log.debug('No data found.')
            return

        try:
            retailer = EquipmentRetailer.objects.get(name=self.plugin.retailer_name)
        except EquipmentRetailer.DoesNotExist:
            log.error(f'Retailer {self.plugin.retailer_name} does not exist')
            return

        for stock_item in data:
            equipment_item_model_class: Model = content_type_map[stock_item.klass].model_class()
            try:
                # Just to check if the item exists.
                equipment_item_model_class.objects.get(pk=stock_item.pk)
            except equipment_item_model_class.DoesNotExist:
                log.error(f"Unable to find equipment item of class {stock_item.klass} and pk {stock_item.pk}")
                continue

            try:
                listing = EquipmentItemListing.objects.get(
                    retailer=retailer,
                    item_content_type = content_type_map[stock_item.klass],
                    item_object_id=stock_item.pk,
                )

                log.debug(f'Updating item listing {listing.pk}')

                EquipmentItemListing.objects.filter(pk=listing.pk).update(
                    name=stock_item.name,
                    sku=stock_item.sku,
                    url=stock_item.url,
                    stock_status=stock_item.stock_status.value,
                    stock_amount=max(0, stock_item.stock_amount),
                    updated=datetime.now(),
                )
            except EquipmentItemListing.DoesNotExist:
                log.debug(f'Creating item listing')

                EquipmentItemListing.objects.create(
                    retailer=retailer,
                    item_content_type=content_type_map[stock_item.klass],
                    item_object_id=stock_item.pk,
                    name=stock_item.name,
                    sku=stock_item.sku,
                    url=stock_item.url,
                    stock_status=stock_item.stock_status.value,
                    stock_amount=max(0, stock_item.stock_amount),
                )
