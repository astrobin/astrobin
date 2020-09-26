from django.db.models import QuerySet, Q
from django.template import Library

from astrobin.models import Gear, Image
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing

register = Library()


@register.filter
def equipment_brand_listings(gear, country):
    # type: (Gear, str) -> QuerySet

    return gear.equipment_brand_listings.filter(
        Q(retailer__countries__icontains=country) |
        Q(retailer__countries=None)
    )


@register.simple_tag
def equipment_brand_listing_utm_tags():
    return "utm_source=astrobin&utm_medium=link&utm_campaign=webshop-integration"


@register.filter
def gear_items_with_listings(image, country):
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
def unique_equipment_brand_listings(image, country):
    # type: (Image, str) -> QuerySet

    pks = []
    gear_items = gear_items_with_listings(image, country)

    for gear_item in gear_items:
        for listing in equipment_brand_listings(gear_item, country):
            pks.append(listing.pk)

    return EquipmentBrandListing.objects.filter(pk__in=pks)
