from django.db.models import QuerySet, Q
from django.template import Library

from astrobin.models import Gear

register = Library()


@register.filter
def equipment_brand_listings(gear, country):
    # type: (Gear, string) -> QuerySet

    return gear.equipment_brand_listings.filter(
        Q(retailer__countries__icontains=country) |
        Q(retailer__countries=None)
    )


@register.simple_tag
def equipment_brand_listing_utm_tags():
    return "utm_source=astrobin&utm_medium=link&utm_campaign=webshop-integration"
