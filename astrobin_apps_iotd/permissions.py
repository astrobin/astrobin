from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free


def may_toggle_submission_image(user, image):
    if user.is_superuser:
        return True, None

    if not user.groups.filter(name='iotd_submitters').exists():
        return False, _("You are not a member of the IOTD Submitters board.")

    if user == image.user:
        return False, _("You cannot submit your own image.")

    if image.is_wip:
        return False, _("Images in the staging area cannot be submitted.")

    if image.user.userprofile.exclude_from_competitions:
        return False, _("This user has chosen to be excluded from competitions.")

    days = settings.IOTD_SUBMISSION_WINDOW_DAYS
    if image.published < datetime.now() - timedelta(days):
        return False, _("You cannot submit an image that was published more than %(max_days)s days ago.") % {
            'max_days': days
        }

    if settings.PREMIUM_RESTRICTS_IOTD:
        if is_free(image.user):
            return False, _("Users with a Free membership cannot participate in the IOTD.")

    # Import here to avoid circular dependency
    from astrobin_apps_iotd.models import IotdSubmission, Iotd

    if Iotd.objects.filter(image=image, date__lte=datetime.now().date()).exists():
        return False, _("This image has already been an IOTD in the past")

    max_allowed = settings.IOTD_SUBMISSION_MAX_PER_DAY
    submitted_today = IotdSubmission.objects.filter(
        submitter=user,
        date__contains=datetime.now().date()).count()
    toggling_on = not IotdSubmission.objects.filter(submitter=user, image=image).exists()
    if submitted_today >= max_allowed and toggling_on:
        return False, _("You have already submitted %(max_allowed)s images today.") % {
            'max_allowed': max_allowed
        }

    return True, None


def may_toggle_vote_image(user, image):
    if user.is_superuser:
        return True, None

    if not user.groups.filter(name='iotd_reviewers').exists():
        return False, _("You are not a member of the IOTD Reviewers board.")

    if user == image.user:
        return False, _("You cannot vote for your own image.")

    if image.is_wip:
        return False, _("Images in the staging area cannot be voted for.")

    if image.user.userprofile.exclude_from_competitions:
        return False, _("This user has chosen to be excluded from competitions.")

    # Import here to avoid circular dependency
    from astrobin_apps_iotd.models import IotdSubmission, IotdVote, Iotd

    if not IotdSubmission.objects.filter(image=image).exists():
        return False, _("You cannot vote for an image that has not been submitted.")

    if user.pk in IotdSubmission.objects.filter(image=image).values_list('submitter', flat=True):
        return False, _("You cannot vote for your own submission.")

    if Iotd.objects.filter(image=image, date__lte=datetime.now().date()).exists():
        return False, _("This image has already been an IOTD in the past")

    days = settings.IOTD_REVIEW_WINDOW_DAYS
    if IotdSubmission.first_for_image(image).date < datetime.now() - timedelta(days):
        return False, _(
            "You cannot vote for an image that has been in the submission queue for more than %(max_days)s days.") % {
                   'max_days': days
               }

    max_allowed = settings.IOTD_REVIEW_MAX_PER_DAY
    reviewed_today = IotdVote.objects.filter(
        reviewer=user,
        date__contains=datetime.now().date()).count()
    toggling_on = not IotdVote.objects.filter(reviewer=user, image=image).exists()
    if reviewed_today >= max_allowed and toggling_on:
        return False, _("You have already voted for %(max_allowed)s images today.") % {
            'max_allowed': max_allowed
        }

    if settings.PREMIUM_RESTRICTS_IOTD:
        if is_free(image.user):
            return False, _("Users with a Free membership cannot participate in the IOTD.")

    return True, None


def may_elect_iotd(user, image):
    if user.is_superuser:
        return True, None

    if not user.groups.filter(name='iotd_judges').exists():
        return False, _("You are not a member of the IOTD Judges board.")

    if user == image.user:
        return False, _("You cannot elect your own image.")

    if image.is_wip:
        return False, _("Images in the staging area cannot be elected.")

    if image.user.userprofile.exclude_from_competitions:
        return False, _("This user has chosen to be excluded from competitions.")

    if settings.PREMIUM_RESTRICTS_IOTD:
        if is_free(image.user):
            return False, _("Users with a Free membership cannot participate in the IOTD.")

    # Import here to avoid circular dependency
    from astrobin_apps_iotd.models import IotdSubmission, IotdVote, Iotd

    if not IotdVote.objects.filter(image=image).exists():
        return False, _("You cannot elect an image that has not been voted.")

    if user.pk in IotdSubmission.objects.filter(image=image).values_list('submitter', flat=True):
        return False, _("You cannot elect your own submission.")

    if user.pk in IotdVote.objects.filter(image=image).values_list('reviewer', flat=True):
        return False, _("You cannot elect an image you voted for.")

    if Iotd.objects.filter(image=image, date__lte=datetime.now().date()).exists():
        return False, _("This image has already been an IOTD in the past")

    days = settings.IOTD_JUDGEMENT_WINDOW_DAYS
    if IotdVote.first_for_image(image).date < datetime.now() - timedelta(days):
        return False, _(
            "You cannot elect an image that has been in the review queue for more than %(max_days)s days.") % {
                   'max_days': days
               }

    max_allowed = settings.IOTD_JUDGEMENT_MAX_PER_DAY
    judged_today = Iotd.objects.filter(
        judge=user,
        created__contains=datetime.now().date()).count()
    toggling_on = not Iotd.objects.filter(image=image).exists()
    if judged_today >= max_allowed and toggling_on:
        return False, _("You have already elected %(max_allowed)s images today.") % {
            'max_allowed': max_allowed
        }

    max_allowed = settings.IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE
    scheduled = Iotd.objects.filter(
        judge=user,
        date__gt=datetime.now().date()).count()
    toggling_on = not Iotd.objects.filter(image=image).exists()
    if scheduled >= max_allowed and toggling_on:
        return False, _("You have already scheduled %(max_allowed)s IOTDs.") % {
            'max_allowed': max_allowed
        }

    return True, None


def may_unelect_iotd(user, image):
    if user.is_superuser:
        return True, None

    if not user.groups.filter(name='iotd_judges').exists():
        return False, _("You are not a member of the IOTD Judges board.")

    # Import here to avoid circular dependency
    from astrobin_apps_iotd.models import Iotd, IotdVote, IotdSubmission

    if user.pk in IotdSubmission.objects.filter(image=image).values_list('submitter', flat=True):
        return False, _("You cannot unelect your own submission.")

    if user.pk in IotdVote.objects.filter(image=image).values_list('reviewer', flat=True):
        return False, _("You cannot unelect an image you voted for.")

    if Iotd.objects.filter(image=image).exclude(judge=user).exists():
        return False, _("You cannot unelect an image elected by another judge.")

    if Iotd.objects.filter(image=image, date__lte=datetime.now().date()).exists():
        return False, _("You cannot unelect a past or current IOTD.")

    return True, None
