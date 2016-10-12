# Python
from datetime import datetime, timedelta

# Django
from django.conf import settings
from django.template import Library
from django.utils.translation import ugettext_lazy as _

# This app
from astrobin_apps_iotd.models import *


register = Library()


@register.inclusion_tag(
    'astrobin_apps_iotd/inclusion_tags/iotd_submit.html',
    takes_context = True)
def iotd_submit(context, image):
    request = context['request']
    enabled = True
    reason = None

    weeks = settings.IOTD_SUBMISSION_WINDOW_WEEKS
    now = datetime.now()
    window_start = now - timedelta(weeks = weeks) 
    if (image.uploaded < window_start):
        enabled = False
        msg = "You cannot submit an image that was uploaded more than %(weeks)s weeks ago."
        reason = _(msg) % {'weeks': weeks}

    if IotdSubmission.objects.filter(submitter = request.user, image = image).exists():
        enabled = False
        msg = "You have already made an IOTD Submission for this image"
        reason = _(msg)

    if IotdSubmission.objects.filter(
        submitter = request.user,
        date__gt = datetime.now().date() - timedelta(1)).count() >= settings.IOTD_SUBMISSION_MAX_PER_DAY:
        enabled = False
        msg = "You have already submitted the maximum allowed number of IOTD Submissions today."
        reason = _(msg)

    if not request.user.groups.filter(name = 'iotd_submitters').exists():
        enabled = False
        msg = "You are not a member of the IOTD Submitters board."
        reason = _(msg)

    if request.user == image.user:
        enabled = False
        msg = "You cannot submit your own image."
        reason = _(msg)

    return {
        'request': context['request'],
        'image': image,
        'iotd_submit_enabled': enabled,
        'iotd_submit_disabled_reason': reason,
    }


@register.filter
def is_iotd_submitter(user):
    return user.groups.filter(name = 'iotd_submitters').exists()
