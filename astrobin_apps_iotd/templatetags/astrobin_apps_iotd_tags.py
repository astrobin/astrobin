from datetime import datetime
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.template import Library
from django.utils.translation import ugettext as _

from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.types.may_not_submit_to_iotd_tp_reason import MayNotSubmitToIotdTpReason
from astrobin_apps_users.services import UserService

register = Library()


@register.filter
def is_iotd_submitter(user) -> bool:
    return UserService(user).is_in_group('iotd_submitters')


@register.filter
def is_iotd_reviewer(user) -> bool:
    return UserService(user).is_in_group('iotd_reviewers')


@register.filter
def is_iotd_judge(user) -> bool:
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
def humanize_may_not_submit_to_iotd_tp_process_reason(reason: str) -> str:
    reason_map = {
        MayNotSubmitToIotdTpReason.NOT_AUTHENTICATED: _(
            "You are not authenticated. Please log in."
        ),
        MayNotSubmitToIotdTpReason.NOT_OWNER: _(
            "You are not the owner of this image."
        ),
        MayNotSubmitToIotdTpReason.IS_FREE: _(
            'Sorry, this feature requires a <a href="%(url)s">paid account</a>.' % {
                'url': 'https://welcome.astrobin.com/pricing'
            }
        ),
        MayNotSubmitToIotdTpReason.NOT_PUBLISHED: _(
            "Unfortunately it's too late: images can be submitted only within %(num_days)s days "
            "after publication." % {
                'num_days': settings.DAYS_AFTER_PUBLICATION_TO_SUBMIT_TO_IOTD_TP
            }
        ),
        MayNotSubmitToIotdTpReason.ALREADY_SUBMITTED: _(
            "This image was already submitted."
        ),
        MayNotSubmitToIotdTpReason.BAD_SUBJECT_TYPE: _(
            "Images with subject type set to 'Gear' or 'Other' are not eligible for IOTD/TP consideration."
        ),
        MayNotSubmitToIotdTpReason.NO_TELESCOPE_OR_CAMERA: _(
            "Images without an imaging telescope and an imaging camera are not eligible for IOTD/TP consideration."
        ),
        MayNotSubmitToIotdTpReason.NO_ACQUISITIONS: _(
            "Images without any acquisition sessions are not eligible for IOTD/TP consideration."
        ),
        MayNotSubmitToIotdTpReason.EXCLUDED_FROM_COMPETITIONS: _(
            "Your settings indicate that you opted to be excluded from competitions."
        ),
        MayNotSubmitToIotdTpReason.BANNED_FROM_COMPETITIONS: _(
            "You are currently serving a ban from competitions on AstroBin."
        )
    }

    try:
        return reason_map[reason]
    except KeyError:
        return _("Unknown reason. This should never happen, please contact us!")


@register.filter
def is_current_or_past_iotd(image: Image):
    return Iotd.objects.filter(image=image, date__lte=datetime.now().date())


@register.simple_tag
def get_iotd() -> Optional[Iotd]:
    iotds: QuerySet = Iotd.objects.filter(date__lte=datetime.now().date()).order_by('-date')
    if iotds:
        return iotds[0]
    return None
