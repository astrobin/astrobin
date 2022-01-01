from django.db.models import QuerySet, Q
from django.template import Library
from fuzzywuzzy import fuzz
from fuzzywuzzy.utils import asciidammit

from astrobin.models import Gear, Image
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_item_listing import EquipmentItemListing

register = Library()


@register.filter
def equipment_brand_listings(gear, country):
    # type: (Gear, str) -> QuerySet

    if country is None:
        return EquipmentBrandListing.objects.none()

    return gear.equipment_brand_listings.filter(
        Q(retailer__countries__icontains=country) |
        Q(retailer__countries=None)
    )


@register.filter
def equipment_item_listings(gear, country):
    # type: (Gear, str) -> QuerySet

    if country is None:
        return EquipmentItemListing.objects.none()

    return gear.equipment_item_listings.filter(
        Q(retailer__countries__icontains=country) |
        Q(retailer__countries=None)
    )


@register.simple_tag
def equipment_listing_url_with_tags(listing: EquipmentBrandListing, source: str) -> str:
    url = listing.url

    if 'brand' in url or 'retailer' in url or 'source' in url:
        return url

    tags_separator = '?'
    if tags_separator in url:
        tags_separator = '&'

    return f'{url}{tags_separator}brand={listing.brand.name}&retailer={listing.retailer.name}&source={source}'


@register.filter
def gear_items_with_brand_listings(image, country):
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
            if equipment_brand_listings(gear_item, country).exists():
                pks.append(gear_item.pk)

    return Gear.objects.filter(pk__in=pks)


@register.filter
def gear_items_with_item_listings(image, country):
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
            if equipment_item_listings(gear_item, country).exists():
                pks.append(gear_item.pk)

    return Gear.objects.filter(pk__in=pks)


@register.filter
def unique_equipment_brand_listings(image, country):
    # type: (Image, str) -> QuerySet

    pks = []
    gear_items = gear_items_with_brand_listings(image, country)

    for gear_item in gear_items:
        for listing in equipment_brand_listings(gear_item, country):
            pks.append(listing.pk)

    return EquipmentBrandListing.objects.filter(pk__in=pks)


@register.filter
def unique_equipment_item_listings(image, country):
    # type: (Image, str) -> QuerySet

    pks = []
    gear_items = gear_items_with_item_listings(image, country)

    for gear_item in gear_items:
        for listing in equipment_item_listings(gear_item, country):
            pks.append(listing.pk)

    return EquipmentItemListing.objects.filter(pk__in=pks)


@register.filter
def is_equipment_moderator(user) -> bool:
    return user.is_authenticated and user.groups.filter(name='equipment_moderators').exists()


@register.filter
def is_own_equipment_migrator(user) -> bool:
    return user.is_authenticated and user.groups.filter(name='own_equipment_migrators').exists()


@register.filter
def can_access_basic_equipment_functions(user) -> bool:
    return is_equipment_moderator(user) or is_own_equipment_migrator(user)


@register.filter
def has_matching_brand_request_query(gear: Gear, q) -> bool:
    brand = gear.make

    if brand in (None, '') or q in (None, ''):
        return False

    similarity = fuzz.partial_ratio(asciidammit(q.lower()), asciidammit(brand.lower()))

    return similarity > 85


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
