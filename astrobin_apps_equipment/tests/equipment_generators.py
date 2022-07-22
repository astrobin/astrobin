from django.template.defaultfilters import slugify

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import Camera, Sensor, Telescope, Mount, Filter, Accessory, Software, \
    EquipmentItemGroup
from astrobin_apps_equipment.models.accessory_base_model import AccessoryType
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.models.equipment_item_listing import EquipmentItemListing
from astrobin_apps_equipment.models.equipment_retailer import EquipmentRetailer
from astrobin_apps_equipment.models.filter_base_model import FilterSize, FilterType
from astrobin_apps_equipment.models.mount_base_model import MountType
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
            website=kwargs.get('website', 'https://www.test-sensor-%s.com/' % random_name),
            quantum_efficiency=kwargs.get('quantum_efficiency', 90),
            pixel_size=kwargs.get('pixel_size', 1.5),
            pixel_width=kwargs.get('pixel_width', 1024),
            pixel_height=kwargs.get('pixel_height', 1024),
            sensor_width=kwargs.get('sensor_width', 1024),
            sensor_height=kwargs.get('sensor_height', 1024),
            full_well_capacity=kwargs.get('full_well_capacity', 30),
            read_noise=kwargs.get('read_noise', 5),
            frame_rate=kwargs.get('frame_rate', 60),
            adc=kwargs.get('adc', 12),
            color_or_mono=kwargs.get('color_or_mono', 'M'),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def camera(**kwargs):
        random_name = Generators.randomString()

        return Camera.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test camera %s' % random_name),
            variant_of=kwargs.get('variant_of', None),
            website=kwargs.get('website', 'https://www.test-camera-%s.com/' % random_name),
            type=kwargs.get('type', CameraType.DEDICATED_DEEP_SKY),
            sensor=kwargs.get('sensor', EquipmentGenerators.sensor()),
            cooled=kwargs.get('cooled', True),
            max_cooling=kwargs.get('max_cooling', 40),
            back_focus=kwargs.get('back_focus', 18),
            modified=kwargs.get('modified', False),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def telescope(**kwargs):
        random_name = Generators.randomString()

        return Telescope.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test telescope %s' % random_name),
            variant_of=kwargs.get('variant_of', None),
            website=kwargs.get('website', 'https://www.test-telescope-%s.com/' % random_name),
            type=kwargs.get('type', TelescopeType.REFRACTOR_ACHROMATIC),
            aperture=kwargs.get('aperture', 75),
            min_focal_length=kwargs.get('min_focal_length', 50),
            max_focal_length=kwargs.get('max_focal_length', 200),
            weight=kwargs.get('weight', 200),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def mount(**kwargs):
        random_name = Generators.randomString()

        return Mount.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test mount %s' % random_name),
            variant_of=kwargs.get('variant_of', None),
            website=kwargs.get('website', 'https://www.test-mount-%s.com/' % random_name),
            type=kwargs.get('type', MountType.GERMAN_EQUATORIAL),
            periodic_error=kwargs.get('periodic_error', 1),
            pec=kwargs.get('pec', True),
            weight=kwargs.get('weight', 40),
            max_payload=kwargs.get('max_payload', 50),
            computerized=kwargs.get('computerized', True),
            slew_speed=kwargs.get('slew_speed', 10),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def filter(**kwargs):
        random_name = Generators.randomString()

        return Filter.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test filter %s' % random_name),
            variant_of=kwargs.get('variant_of', None),
            website=kwargs.get('website', 'https://www.test-filter-%s.com/' % random_name),
            type=kwargs.get('type', FilterType.L),
            bandwidth=kwargs.get('bandwidth', 12),
            size=kwargs.get('size', FilterSize.ROUND_50_MM),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def accessory(**kwargs):
        random_name = Generators.randomString()

        return Accessory.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test software %s' % random_name),
            type=kwargs.get('type', AccessoryType.OTHER),
            variant_of=kwargs.get('variant_of', None),
            website=kwargs.get('website', 'https://www.test-accessory-%s.com/' % random_name),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def software(**kwargs):
        random_name = Generators.randomString()

        return Software.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test software %s' % random_name),
            variant_of=kwargs.get('variant_of', None),
            website=kwargs.get('website', 'https://www.test-software-%s.com/' % random_name),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def equipment_item_group(**kwargs):
        return EquipmentItemGroup.objects.create(
            klass=kwargs.get('klass', EquipmentItemKlass.TELESCOPE),
            name=Generators.randomString()
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
    def equipment_brand_listing(**kwargs):
        brand = kwargs.get('brand', EquipmentGenerators.equipment_brand())
        retailer = kwargs.get('retailer', EquipmentGenerators.equipment_retailer())

        return EquipmentBrandListing.objects.create(
            brand=brand,
            retailer=retailer,
            url=kwargs.get('url', "%s/shop/%s" % (retailer.website, slugify(brand))),
        )

    @staticmethod
    def equipment_item_listing(**kwargs):
        brand = kwargs.get('brand', EquipmentGenerators.equipment_brand())
        retailer = kwargs.get('retailer', EquipmentGenerators.equipment_retailer())

        return EquipmentItemListing.objects.create(
            name=kwargs.get('name', Generators.randomString()),
            retailer=retailer,
            url=kwargs.get('url', "%s/shop/%s" % (retailer.website, slugify(brand))),
        )
