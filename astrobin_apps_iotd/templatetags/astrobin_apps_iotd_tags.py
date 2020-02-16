from datetime import datetime

from django.template import Library

from astrobin_apps_iotd.models import IotdSubmission, IotdVote, Iotd
from astrobin_apps_iotd.permissions import may_toggle_submission_image, may_toggle_vote_image, may_elect_iotd, \
    may_unelect_iotd

register = Library()


# Roles

@register.filter
def is_iotd_submitter(user):
    return user.groups.filter(name = 'iotd_submitters').exists()


@register.filter
def is_iotd_reviewer(user):
    return user.groups.filter(name = 'iotd_reviewers').exists()


@register.filter
def is_iotd_judge(user):
    return user.groups.filter(name = 'iotd_judges').exists()


# Permissions

@register.filter
def may_toggle_submission(user, image):
    may, reason = may_toggle_submission_image(user, image)
    return may


@register.filter
def may_not_toggle_submission_reason(user, image):
    may, reason = may_toggle_submission_image(user, image)
    return reason


@register.filter
def may_toggle_vote(user, image):
    may, reason = may_toggle_vote_image(user, image)
    return may


@register.filter
def may_not_toggle_vote_reason(user, image):
    may, reason = may_toggle_vote_image(user, image)
    return reason


@register.filter
def may_elect(user, image):
    may, reason = may_elect_iotd(user, image)
    return may


@register.filter
def may_unelect(user, image):
    may, reason = may_unelect_iotd(user, image)
    return may


@register.filter
def may_not_elect_reason(user, image):
    may, reason = may_elect_iotd(user, image)
    return reason


@register.filter
def may_not_unelect_reason(user, image):
    may, reason = may_unelect_iotd(user, image)
    return reason


# Statuses

@register.filter
def has_submitted(user, image):
    return IotdSubmission.objects.filter(image = image, submitter = user).exists()


@register.filter
def has_voted(user, image):
    return IotdVote.objects.filter(image = image, reviewer = user).exists()


@register.filter
def is_submitted_by(image, user):
    return IotdSubmission.objects.filter(image = image, submitter = user).exists()


@register.filter
def submissions_count(image):
    return IotdSubmission.objects.filter(image = image).count()


@register.filter
def votes_count(image):
    return IotdVote.objects.filter(image = image).count()


@register.filter
def is_iotd(image):
    return Iotd.objects.filter(image = image).exists()


@register.filter
def is_current_or_past_iotd(image):
    return Iotd.objects.filter(image = image, date__lte = datetime.now().date())


@register.filter
def iotd_submissions_today(user):
    return IotdSubmission.objects.filter(submitter = user, date__contains = datetime.now().date()).count()


@register.filter
def iotd_votes_today(user):
    return IotdVote.objects.filter(reviewer = user, date__contains = datetime.now().date()).count()


@register.filter
def iotd_elections_today(user):
    return Iotd.objects.filter(judge = user, created__contains = datetime.now().date()).count()


# Getters

@register.filter
def iotd_date_for_image(image):
    try:
        iotd = Iotd.objects.get(image = image)
        return iotd.date
    except Iotd.DoesNotExist:
        return ""

@register.assignment_tag
def get_iotd():
    iotds = Iotd.objects.filter(date__lte = datetime.now().date()).order_by('-date')
    if iotds:
        return iotds[0]
    return None
