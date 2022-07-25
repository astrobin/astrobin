from typing import List

from annoying.functions import get_object_or_None
from django.template import Library
from pybb.models import Forum

from astrobin_apps_equipment.models import Accessory, Camera, EquipmentItem, Filter, Mount, Sensor, Software, Telescope
from astrobin_apps_forum.services import ForumService
from common.services import AppRedirectionService

register = Library()


@register.filter
def exclude_empty_forums_in_category(forums: List[Forum], category_slug: str) -> List[Forum]:
    return [x for x in forums if x.category.slug != category_slug or x.topic_count > 0]


@register.simple_tag
def forum_equipment_item_url(forum: Forum) -> str:
    item: EquipmentItem = ForumService(forum).get_equipment_item()
    if item:
        return AppRedirectionService.redirect(f'/equipment/explorer/{item.klass.lower()}/{item.id}/{item.slug}');
