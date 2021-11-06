from django.template.defaultfilters import slugify

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import Camera, Sensor, Telescope
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_item_listing import EquipmentItemListing
from astrobin_apps_equipment.models.equipment_retailer import EquipmentRetailer
from astrobin_apps_equipment.models.telescope_base_model import TelescopeType


class EquipmentGenerators:
    def __init__(self):
        pass

    @staticmethod
    def brand(**kwargs):
        random_name = Generators.randomString()

        return EquipmentBrand.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            name=kwargs.get('name', 'Test brand %s' % random_name),
            website=kwargs.get('website', 'https://www.test-brand-%s.com/' % random_name),
            logo=kwargs.pop('logo', 'images/test-brand-logo.jpg'),
        )

    @staticmethod
    def sensor(**kwargs):
        random_name = Generators.randomString()

        return Sensor.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test sensor %s' % random_name),
            quantum_efficiency=kwargs.get('quantum_efficiency', 90),
            pixel_size=kwargs.get('pixel_size', 1.5),
            pixel_width=kwargs.get('pixel_width', 1024),
            pixel_height=kwargs.get('pixel_height', 1024),
            sensor_width=kwargs.get('sensor_width', 1024),
            sensor_height=kwargs.get('sensor_height', 1024),
            full_well_capacity=kwargs.get('full_well_capacity', 30000),
            read_noise=kwargs.get('read_noise', 5),
            frame_rate=kwargs.get('frame_rate', 60),
            adc=kwargs.get('adc', 12),
            color_or_mono=kwargs.get('color_or_mono', 'M'),
        )

    @staticmethod
    def camera(**kwargs):
        random_name = Generators.randomString()

        return Camera.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test camera %s' % random_name),
            type=kwargs.get('type', CameraType.DEDICATED_DEEP_SKY),
            sensor=kwargs.get('sensor', EquipmentGenerators.sensor()),
            cooled=kwargs.get('cooled', True),
            max_cooling=kwargs.get('max_cooling', 40),
            back_focus=kwargs.get('back_focus', 18),
            modified=kwargs.get('modified', False),
        )

    @staticmethod
    def telescope(**kwargs):
        random_name = Generators.randomString()

        return Telescope.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test telescope %s' % random_name),
            type=kwargs.get('type', TelescopeType.REFRACTOR_ACHROMATIC),
            aperture=kwargs.get('aperture', 75),
            min_focal_length=kwargs.get('min_focal_length', 50),
            max_focal_length=kwargs.get('max_focal_length', 200),
            weight=kwargs.get('weight', 200),
        )

    @staticmethod
    def equipment_brand():
        return EquipmentBrand.objects.create(
            name=Generators.randomString()
        )

    @staticmethod
    def equipment_retailer():
        return EquipmentRetailer.objects.create(
            name=Generators.randomString(),
            website="https://www.%s.com" % Generators.randomString(),
        )

    @staticmethod
    def equipment_brand_listing():
        brand = EquipmentGenerators.equipment_brand()
        retailer = EquipmentGenerators.equipment_retailer()

        return EquipmentBrandListing.objects.create(
            brand=brand,
            retailer=retailer,
            url="%s/shop/%s" % (retailer.website, slugify(brand)),
        )

    @staticmethod
    def equipment_item_listing():
        brand = EquipmentGenerators.equipment_brand()
        retailer = EquipmentGenerators.equipment_retailer()

        return EquipmentItemListing.objects.create(
            name=Generators.randomString(),
            retailer=retailer,
            url="%s/shop/%s" % (retailer.website, slugify(brand)),
        )
