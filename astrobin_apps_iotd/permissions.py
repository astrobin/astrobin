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
        return False, _("You cannot submit an image that was uploaded more than %(max_weeks)s weeks ago.") % {
            'max_weeks': weeks
        }

    # Import here to avoid circular dependency
    from astrobin_apps_iotd.models import IotdSubmission, Iotd

    if IotdSubmission.objects.filter(submitter = user, image = image).exists():
        return False, _("You have already submitted this image.")

    if Iotd.objects.filter(image = image, date__lte = datetime.now().date()).exists():
        return False, _("This image has already been an IOTD in the past")

    max_allowed = settings.IOTD_SUBMISSION_MAX_PER_DAY
    submitted_today = IotdSubmission.objects.filter(
        submitter = user,
        date__gt = datetime.now().date() - timedelta(1)).count()
    if submitted_today >= max_allowed:
        return False, _("You have already submitted %(max_allowed)s images today.") % {
            'max_allowed': max_allowed
        }

    return True, None


def may_toggle_vote_image(user, image):
    if not user.groups.filter(name = 'iotd_reviewers').exists():
        return False, _("You are not a member of the IOTD Reviewers board.")

    if user == image.user:
        return False, _("You cannot vote for your own image.")

    if image.is_wip:
        return False, _("Images in the staging area cannot be voted for.")

    # Import here to avoid circular dependency
    from astrobin_apps_iotd.models import IotdSubmission, IotdVote, Iotd

    if not IotdSubmission.objects.filter(image = image).exists():
        return False, _("You cannot vote for an image that has not been submitted.")

    if user.pk in IotdSubmission.objects.filter(image = image).values_list('submitter', flat = True):
        return False, _("You cannot vote for your own submission.")

    if Iotd.objects.filter(image = image, date__lte = datetime.now().date()).exists():
        return False, _("This image has already been an IOTD in the past")

    weeks = settings.IOTD_REVIEW_WINDOW_WEEKS
    if IotdSubmission.first_for_image(image).date < datetime.now() - timedelta(weeks = weeks):
        return False, _("You cannot vote for an image that has been in the submission queue for more than %(max_weeks)s weeks.") % {
            'max_weeks': weeks
        }

    max_allowed = settings.IOTD_REVIEW_MAX_PER_DAY
    reviewed_today = IotdVote.objects.filter(
        reviewer = user,
        date__gt = datetime.now().date() - timedelta(1)).count()
    if reviewed_today >= max_allowed:
        return False, _("You have already voted for %(max_allowed)s images today.") % {
            'max_allowed': max_allowed
        }

    return True, None


def may_elect_iotd(user, image):
    if not user.groups.filter(name = 'iotd_judges').exists():
        return False, _("You are not a member of the IOTD Judges board.")

    if user == image.user:
        return False, _("You cannot elect your own image.")

    if image.is_wip:
        return False, _("Images in the staging area cannot be elected.")

    # Import here to avoid circular dependency
    from astrobin_apps_iotd.models import IotdSubmission, IotdVote, Iotd

    if not IotdVote.objects.filter(image = image).exists():
        return False, _("You cannot elect an image that has not been voted.")

    if user.pk in IotdSubmission.objects.filter(image = image).values_list('submitter', flat = True):
        return False, _("You cannot elect your own submission.")

    if user.pk in IotdVote.objects.filter(image = image).values_list('reviewer', flat = True):
        return False, _("You cannot elect an image you voted for.")

    if Iotd.objects.filter(image = image, date__lte = datetime.now().date()).exists():
        return False, _("This image has already been an IOTD in the past")

    weeks = settings.IOTD_JUDGEMENT_WINDOW_WEEKS
    if IotdVote.first_for_image(image).date < datetime.now() - timedelta(weeks = weeks):
        return False, _("You cannot elect an image that has been in the review queue for more than %(max_weeks)s weeks.") % {
            'max_weeks': weeks
        }

    max_allowed = settings.IOTD_JUDGEMENT_MAX_PER_DAY
    judged_today = Iotd.objects.filter(
        judge = user,
        created__gt = datetime.now().date() - timedelta(1)).count()
    if judged_today >= max_allowed:
        return False, _("You have already elected %(max_allowed)s images today.") % {
            'max_allowed': max_allowed
        }

    return True, None


def may_unelect_iotd(user, image):
    if not user.groups.filter(name = 'iotd_judges').exists():
        return False, _("You are not a member of the IOTD Judges board.")

    # Import here to avoid circular dependency
    from astrobin_apps_iotd.models import Iotd, IotdVote, IotdSubmission

    if user.pk in IotdSubmission.objects.filter(image = image).values_list('submitter', flat = True):
        return False, _("You cannot unelect your own submission.")

    if user.pk in IotdVote.objects.filter(image = image).values_list('reviewer', flat = True):
        return False, _("You cannot unelect an image you voted for.")

    if Iotd.objects.filter(image = image).exclude(judge = user).exists():
        return False, _("You cannot unelect an image elected by another judge.")

    if Iotd.objects.filter(image = image, date__lte = datetime.now().date()).exists():
        return False, _("You cannot unelect a past or current IOTD.")

    return True, None
