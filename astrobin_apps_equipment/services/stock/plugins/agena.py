import logging
import os
from typing import List, Tuple
from xml.etree import ElementTree

import requests

from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.services.stock.plugins import StockImporterPluginInterface
from astrobin_apps_equipment.types import StockStatus
from astrobin_apps_equipment.types.stock_interface import StockInterface

log = logging.getLogger(__name__)


class AgenaStockImporterPlugin(StockImporterPluginInterface):
    retailer_name = 'Agena Astro'
    url = os.environ.get('STOCK_URL_AGENA')

    def parse_astrobin_id(self, astrobin_id: str) -> Tuple[int, EquipmentItemKlass]:
        klass_map = {
            'T': EquipmentItemKlass.TELESCOPE,
            'C': EquipmentItemKlass.CAMERA,
            'M': EquipmentItemKlass.MOUNT,
            'F': EquipmentItemKlass.FILTER,
            'A': EquipmentItemKlass.ACCESSORY,
            'S': EquipmentItemKlass.SENSOR,
        }

        klass_initial = astrobin_id[0]

        try:
            klass = klass_map[klass_initial]
        except KeyError as e:
            log.error(f'Invalid klass initial {klass_initial} in {astrobin_id}')
            raise e

        try:
            pk = int(astrobin_id.replace(klass_initial, ''))
        except ValueError as e:
            log.error(f'Invalid AstroBin ID: {astrobin_id}')
            raise e

        return pk, klass

    def parse_stock_status(self, stock_status_str) -> StockStatus:
        stock_status_map = {
            'Unknown': StockStatus.UNKNOWN,
            'Back Order': StockStatus.BACK_ORDER,
            'In Stock': StockStatus.IN_STOCK,
            'Out of Stock': StockStatus.OUT_OF_STOCK,
        }

        try:
            return stock_status_map[stock_status_str]
        except KeyError as e:
            log.error(f'Invalid stock status: {stock_status_str}')
            raise e

    def __parse(self, xml_str: str) -> List[StockInterface]:
        root = ElementTree.fromstring(xml_str)
        products = root.find('channel').find('products').findall("product")
        stock_list = []

        for product in products:
            try:
                astrobin_id = product.find('ca_astrobin_product_id').text
                pk, klass = self.parse_astrobin_id(astrobin_id)
                name = product.find('name').text
                sku = product.find('sku').text
                url = product.find('product_url').text
                stock_status_str = product.find('stock_status').text
                stock_status = self.parse_stock_status(stock_status_str)
                stock_amount = int(product.find('stock_qty').text)
                stock_obj = StockInterface(pk, klass, name, sku, url, stock_status, stock_amount)
                stock_list.append(stock_obj)
            except Exception as e:
                log.error(str(e))
                continue

        return stock_list

    def fetch_data(self) -> List[StockInterface]:
        if not self.url:
            log.error('No URL set for Agena Astro')
            return []

        try:
            response = requests.get(self.url)
            return self.__parse(response.content)
        except Exception as e:
            log.error(e)
            return []

