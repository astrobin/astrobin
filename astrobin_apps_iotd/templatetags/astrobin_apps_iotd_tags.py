from datetime import datetime

from django.contrib.auth.models import User
from django.template import Library

from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd
from astrobin_apps_iotd.services import IotdService

register = Library()


@register.filter
def is_iotd_submitter(user):
    return user.groups.filter(name='iotd_submitters').exists()


@register.filter
def is_iotd_reviewer(user):
    return user.groups.filter(name='iotd_reviewers').exists()


@register.filter
def is_iotd_judge(user):
    return user.groups.filter(name='iotd_judges').exists()


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
