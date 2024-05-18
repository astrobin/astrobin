from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import (
    Camera, EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem, EquipmentItemMarketplaceOffer,
    Sensor, Telescope, Mount, Filter,
    Accessory, Software,
    EquipmentItemGroup,
)
from astrobin_apps_equipment.models.accessory_base_model import AccessoryType
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.models.equipment_item_listing import EquipmentItemListing
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_equipment.models.equipment_retailer import EquipmentRetailer
from astrobin_apps_equipment.models.filter_base_model import FilterSize, FilterType
from astrobin_apps_equipment.models.mount_base_model import MountType
from astrobin_apps_equipment.models.telescope_base_model import TelescopeType
from astrobin_apps_equipment.types.marketplace_line_item_condition import MarketplaceLineItemCondition
from common.services import DateTimeService


class EquipmentGenerators:
    def __init__(self):
        pass

    @staticmethod
    def brand(**kwargs):
        random_name = Generators.random_string()

        return EquipmentBrand.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            name=kwargs.get('name', 'Test brand %s' % random_name),
            website=kwargs.get('website', 'https://www.test-brand-%s.com/' % random_name),
            logo=kwargs.pop('logo', 'images/test-brand-logo.jpg'),
        )

    @staticmethod
    def sensor(**kwargs):
        random_name = Generators.random_string()

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
        random_name = Generators.random_string()

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
            reviewed_by=kwargs.get('reviewed_by', None),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def telescope(**kwargs):
        random_name = Generators.random_string()
        created_by = kwargs.get('created_by')
        brand = kwargs.get('brand')

        if created_by is None:
            created_by = Generators.user()

        if brand is None:
            brand = EquipmentGenerators.brand()

        return Telescope.objects.create(
            created_by=created_by,
            brand=brand,
            name=kwargs.get('name', 'Test telescope %s' % random_name),
            variant_of=kwargs.get('variant_of', None),
            website=kwargs.get('website', 'https://www.test-telescope-%s.com/' % random_name),
            type=kwargs.get('type', TelescopeType.REFRACTOR_ACHROMATIC),
            aperture=kwargs.get('aperture', 75),
            min_focal_length=kwargs.get('min_focal_length', 50),
            max_focal_length=kwargs.get('max_focal_length', 200),
            weight=kwargs.get('weight', 200),
            reviewed_by=kwargs.get('reviewed_by', None),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def mount(**kwargs):
        random_name = Generators.random_string()

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
            reviewed_by=kwargs.get('reviewed_by', None),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def filter(**kwargs):
        random_name = Generators.random_string()

        return Filter.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test filter %s' % random_name),
            variant_of=kwargs.get('variant_of', None),
            website=kwargs.get('website', 'https://www.test-filter-%s.com/' % random_name),
            type=kwargs.get('type', FilterType.L),
            bandwidth=kwargs.get('bandwidth', 12),
            size=kwargs.get('size', FilterSize.ROUND_50_MM),
            reviewed_by=kwargs.get('reviewed_by', None),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def accessory(**kwargs):
        random_name = Generators.random_string()

        return Accessory.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test accessory %s' % random_name),
            type=kwargs.get('type', AccessoryType.OTHER),
            variant_of=kwargs.get('variant_of', None),
            website=kwargs.get('website', 'https://www.test-accessory-%s.com/' % random_name),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def software(**kwargs):
        random_name = Generators.random_string()

        return Software.objects.create(
            created_by=kwargs.get('created_by', Generators.user()),
            brand=kwargs.get('brand', EquipmentGenerators.brand()),
            name=kwargs.get('name', 'Test software %s' % random_name),
            variant_of=kwargs.get('variant_of', None),
            website=kwargs.get('website', 'https://www.test-software-%s.com/' % random_name),
            reviewed_by=kwargs.get('reviewed_by', None),
            reviewer_decision=kwargs.get('reviewer_decision', None),
            assignee=kwargs.get('assignee', None),
            frozen_as_ambiguous=kwargs.get('frozen_as_ambiguous', None),
        )

    @staticmethod
    def equipment_item_group(**kwargs):
        return EquipmentItemGroup.objects.create(
            klass=kwargs.get('klass', EquipmentItemKlass.TELESCOPE),
            name=Generators.random_string()
        )

    @staticmethod
    def equipment_brand():
        return EquipmentBrand.objects.create(
            name=Generators.random_string()
        )

    @staticmethod
    def equipment_retailer():
        return EquipmentRetailer.objects.create(
            name=Generators.random_string(),
            website="https://www.%s.com" % Generators.random_string(),
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
        item_content_object = kwargs.get('item_content_object', EquipmentGenerators.telescope())

        return EquipmentItemListing.objects.create(
            name=kwargs.get('name', Generators.random_string()),
            retailer=retailer,
            item_content_object=item_content_object,
            url=kwargs.get('url', "%s/shop/%s" % (retailer.website, slugify(brand))),
        )

    @staticmethod
    def marketplace_line_item(**kwargs):
        user = kwargs.get('user')
        listing = kwargs.get('listing')
        item = kwargs.get('item')

        if user is None:
            user = Generators.user()

        if listing is None:
            listing = EquipmentGenerators.marketplace_listing()

        if item is None:
            item = EquipmentGenerators.telescope()

        return EquipmentItemMarketplaceListingLineItem.objects.create(
            user=user,
            listing=listing,
            price=kwargs.get('price', 1000),
            condition=kwargs.get('condition', MarketplaceLineItemCondition.NEW),
            item_object_id=item.pk,
            item_content_type=ContentType.objects.get_for_model(item),
            sold=kwargs.get('sold', None),
            sold_to=kwargs.get('sold_to', None),
        )

    @staticmethod
    def marketplace_listing(**kwargs):
        user = kwargs.get('user')

        if user is None:
            user = Generators.user()

        return EquipmentItemMarketplaceListing.objects.create(
            user=user,
            title=kwargs.get('title', Generators.random_string()),
            expiration=kwargs.get('expiration', DateTimeService.now() + timedelta(days=30)),
        )

    @staticmethod
    def marketplace_offer(**kwargs):
        listing = kwargs.get('listing')
        line_item = kwargs.get('line_item')
        user = kwargs.get('user')

        if line_item is None:
            line_item = EquipmentGenerators.marketplace_line_item()

        if user is None:
            user = Generators.user()

        return EquipmentItemMarketplaceOffer.objects.create(
            listing=listing,
            line_item=line_item,
            user=user,
            amount=kwargs.get('amount', 900),
            status=kwargs.get('status', EquipmentItemMarketplaceOfferStatus.PENDING.value),
        )
