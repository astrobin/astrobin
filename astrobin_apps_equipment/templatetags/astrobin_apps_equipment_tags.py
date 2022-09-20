from typing import List

from django.db.models import QuerySet, Q
from django.template import Library

from astrobin.models import Gear, Image
from astrobin.services.gear_service import GearService
from astrobin_apps_equipment.models import EquipmentBrand
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_item_listing import EquipmentItemListing
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_users.services import UserService
from common.constants import GroupName

register = Library()


@register.filter
def equipment_brand_listings_for_legacy_gear(gear: Gear, country: str) -> QuerySet:
    if country is None:
        return EquipmentBrandListing.objects.none()

    return gear.equipment_brand_listings.filter(
        Q(retailer__countries__icontains=country) |
        Q(retailer__countries=None)
    )


@register.filter
def equipment_brand_listings_by_item(item, country: str) -> QuerySet:
    return EquipmentService.equipment_brand_listings_by_item(item, country)


@register.filter
def equipment_item_listings(item, country: str) -> QuerySet:
    return EquipmentService.equipment_item_listings(item, country)


@register.filter
def equipment_item_listings_for_legacy_gear(gear, country):
    # type: (Gear, str) -> QuerySet

    if country is None:
        return EquipmentItemListing.objects.none()

    return gear.equipment_item_listings.filter(
        Q(retailer__countries__icontains=country) |
        Q(retailer__countries=None)
    )


@register.simple_tag
def equipment_brand_listing_url_with_tags(listing: EquipmentBrandListing, source: str) -> str:
    url = listing.url

    if 'brand' in url or 'retailer' in url or 'source' in url:
        return url

    tags_separator = '?'
    if tags_separator in url:
        tags_separator = '&'

    return f'{url}{tags_separator}brand={listing.brand.name}&retailer={listing.retailer.name}&source={source}'


@register.simple_tag
def equipment_item_listing_url_with_tags(listing: EquipmentItemListing, source: str) -> str:
    url = listing.url

    if 'brand' in url or 'name' in url or 'retailer' in url or 'source' in url:
        return url

    tags_separator = '?'
    if tags_separator in url:
        tags_separator = '&'

    return f'{url}{tags_separator}brand={listing.item_content_object.brand.name}&name={listing.item_content_object.name}&retailer={listing.retailer.name}&source={source}'


@register.filter
def legacy_gear_items_with_brand_listings(image, country):
    # type: (Image, str) -> QuerySet

    pks = []

    for gear_type in (
            'imaging_telescopes',
            'guiding_telescopes',
            'imaging_cameras',
            'guiding_cameras',
            'mounts',
            'filters',
            'focal_reducers',
            'accessories',
            'software'
    ):
        for gear_item in getattr(image, gear_type).all():
            if equipment_brand_listings_for_legacy_gear(gear_item, country).exists():
                pks.append(gear_item.pk)

    return Gear.objects.filter(pk__in=pks)


@register.filter
def legacy_gear_items_with_item_listings(image, country):
    # type: (Image, str) -> QuerySet

    pks = []

    for gear_type in (
            'imaging_telescopes',
            'guiding_telescopes',
            'imaging_cameras',
            'guiding_cameras',
            'mounts',
            'filters',
            'focal_reducers',
            'accessories',
            'software'
    ):
        for gear_item in getattr(image, gear_type).all():
            if equipment_item_listings_for_legacy_gear(gear_item, country).exists():
                pks.append(gear_item.pk)

    return Gear.objects.filter(pk__in=pks)


@register.filter
def equipment_items_with_brand_listings(image: Image, country: str) -> List:
    items = []

    for item_type in (
            'imaging_telescopes_2',
            'guiding_telescopes_2',
            'imaging_cameras_2',
            'guiding_cameras_2',
            'mounts_2',
            'filters_2',
            'accessories_2',
            'software_2'
    ):
        for item in getattr(image, item_type).all():
            if equipment_brand_listings(item.brand, country).exists():
                items.append(item)

    return items


@register.filter
def unique_equipment_brand_listings_for_legacy_gear(image, country):
    # type: (Image, str) -> QuerySet

    pks = []
    gear_items = legacy_gear_items_with_brand_listings(image, country)

    for gear_item in gear_items:
        for listing in equipment_brand_listings_for_legacy_gear(gear_item, country):
            pks.append(listing.pk)

    return EquipmentBrandListing.objects.filter(pk__in=pks)


@register.filter
def unique_equipment_brand_listings(image: Image, country: str) -> List[EquipmentBrandListing]:
    listings = []
    items = equipment_items_with_brand_listings(image, country)

    for item in items:
        for listing in equipment_brand_listings(item.brand, country):
            listings.append(listing)

    return listings


@register.filter
def unique_equipment_item_listings_for_legacy_gear(image, country):
    # type: (Image, str) -> QuerySet

    pks = []
    gear_items = legacy_gear_items_with_item_listings(image, country)

    for gear_item in gear_items:
        for listing in equipment_item_listings_for_legacy_gear(gear_item, country):
            pks.append(listing.pk)

    return EquipmentItemListing.objects.filter(pk__in=pks)


@register.filter
def is_equipment_moderator(user) -> bool:
    return UserService(user).is_in_group(GroupName.EQUIPMENT_MODERATORS)


@register.filter
def is_own_equipment_migrator(user) -> bool:
    return UserService(user).is_in_group(GroupName.OWN_EQUIPMENT_MIGRATORS)


@register.filter
def can_access_basic_equipment_functions(user) -> bool:
    return True

@register.filter
def equipment_list_has_items(equipment_list) -> bool:
    return (
        len(equipment_list['imaging_telescopes']) > 0 or
        len(equipment_list['imaging_cameras']) > 0 or
        len(equipment_list['mounts']) > 0 or
        len(equipment_list['filters']) > 0 or
        len(equipment_list['accessories']) > 0 or
        len(equipment_list['software']) > 0 or
        len(equipment_list['guiding_telescopes']) > 0 or
        len(equipment_list['guiding_cameras']) > 0
    )


@register.filter
def image_has_legacy_gear(image: Image) -> bool:
    return GearService.image_has_legacy_gear(image)


@register.filter
def image_has_equipment_items(image: Image) -> bool:
    return EquipmentService.image_has_equipment_items(image)
