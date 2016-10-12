# Python
from datetime import datetime, timedelta

# Django
from django.conf import settings
from django.template import Library
from django.utils.translation import ugettext_lazy as _

# This app
from astrobin_apps_iotd.models import *
from astrobin_apps_iotd.permissions import *


register = Library()


@register.inclusion_tag(
    'astrobin_apps_iotd/inclusion_tags/iotd_submit.html',
    takes_context = True)
def iotd_submit(context, image):
    request = context['request']
    enabled, reason = may_submit_image(request.user, image)

    return {
        'request': request,
        'image': image,
        'iotd_submit_enabled': enabled,
        'iotd_submit_disabled_reason': reason,
    }


@register.filter
def is_iotd_submitter(user):
    return user.groups.filter(name = 'iotd_submitters').exists()
