from datetime import datetime

from django.contrib.auth.models import User
from django.core.cache import cache
from django.template import Library

from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd, IotdStats
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_users.services import UserService

register = Library()


@register.filter
def is_iotd_submitter(user):
    return UserService(user).is_in_group('iotd_submitters')


@register.filter
def is_iotd_reviewer(user):
    return UserService(user).is_in_group('iotd_reviewers')


@register.filter
def is_iotd_judge(user):
    return UserService(user).is_in_group('iotd_judges')


@register.filter
def may_submit_to_iotd_tp_process(user: User, image: Image) -> bool:
    may, reason = IotdService.may_submit_to_iotd_tp_process(user, image)
    return may


@register.filter
def may_submit_to_iotd_tp_process_reason(user: User, image: Image) -> str:
    may, reason = IotdService.may_submit_to_iotd_tp_process(user, image)
    return reason


@register.filter
def is_current_or_past_iotd(image):
    return Iotd.objects.filter(image=image, date__lte=datetime.now().date())


@register.simple_tag
def get_iotd():
    iotds = Iotd.objects.filter(date__lte=datetime.now().date()).order_by('-date')
    if iotds:
        return iotds[0]
    return None


@register.simple_tag
def iotd_stats():
    cache_key = 'iotd_stats'

    stats_dict = cache.get(cache_key)

    if not stats_dict:
        stats = IotdStats.objects.first()
        stats_dict = {f: getattr(stats, f) for f in [field.name for field in stats._meta.fields]} if stats else None
        cache.set(cache_key, stats_dict, 60 * 60 * 24)

    return stats_dict
