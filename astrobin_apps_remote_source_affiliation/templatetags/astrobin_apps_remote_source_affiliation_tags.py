from typing import Union

from annoying.functions import get_object_or_None
from django.template import Library
from django.utils.safestring import mark_safe

from astrobin_apps_remote_source_affiliation.models import RemoteSourceAffiliate
from astrobin_apps_remote_source_affiliation.services.remote_source_affiliation_service import \
    RemoteSourceAffiliationService

register = Library()


@register.simple_tag
def remote_source_affiliates():
    return mark_safe([str(x) for x in RemoteSourceAffiliate.objects.all().values_list('code', flat=True)])


@register.filter
def is_remote_source_affiliate(code):
    # type: (unicode) -> bool
   return RemoteSourceAffiliationService.is_remote_source_affiliate(code)


@register.filter
def remote_source_affiliate_url(code: str) -> Union[str, None]:
    remote_source: Union[RemoteSourceAffiliate, None] = get_object_or_None(RemoteSourceAffiliate, code=code)

    if remote_source is None:
        return None

    if '?' in remote_source.url:
        return remote_source.url

    return f'{remote_source.url}?utm_source=astrobin&utm_medium=technical-card&utm_campaign=hosting-facility'


@register.filter
def remote_source_affiliate_image(code):
    # type: (unicode) -> unicode|None

    remote_source = get_object_or_None(RemoteSourceAffiliate, code=code)  # type: RemoteSourceAffiliate

    if remote_source is None:
        return None

    try:
        return remote_source.image_file.url
    except ValueError:
        return None
