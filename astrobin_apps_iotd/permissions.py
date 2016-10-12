# Python
from datetime import datetime, timedelta

# Django
from django.conf import settings
from django.utils.translation import ugettext_lazy as _



def may_submit_image(user, image):
    if not user.groups.filter(name = 'iotd_submitters').exists():
        return False, _("You are not a member of the IOTD Submitters board.")

    if user == image.user:
        return False, _("You cannot submit your own image.")

    if image.is_wip:
        return False, _("Images in the staging area cannot be submitted.")

    weeks = settings.IOTD_SUBMISSION_WINDOW_WEEKS
    if image.uploaded < datetime.now() - timedelta(weeks = weeks):
        return False, _("You cannot submit an image that was uploaded more than %(weeks)s weeks ago.") % {
            weeks: weeks
        }

    # Import here to avoid circular dependency
    from astrobin_apps_iotd.models import IotdSubmission

    if IotdSubmission.objects.filter(submitter = user, image = image).count() > 0:
        return False, _("You have already submitted this image.")

    max_allowed = settings.IOTD_SUBMISSION_MAX_PER_DAY
    submitted_today = IotdSubmission.objects.filter(
        submitter = user,
        date__gt = datetime.now().date() - timedelta(1)).count()
    if submitted_today >= max_allowed:
        return False, _("You have already submitted %(max_allowed)s images today.") % {
            max_allowed: max_allowed
        }

    return True, None
