# Python
import datetime

from django.contrib.auth.decorators import login_required
# Django
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.http import require_POST
# Other
from subscription.models import Subscription, UserSubscription

# This app
from rawdata.utils import SUBSCRIPTION_NAMES


@login_required
@require_POST
def atom_activate(request):
    # First unsubscribe from other Rawdata plans
    subs = UserSubscription.objects.filter(
        user=request.user,
        subscription__name__in=SUBSCRIPTION_NAMES)
    for sub in subs:
        sub.active = False
        sub.cancelled = True
        sub.unsubscribe()
        sub.save()

    us, created = UserSubscription.objects.get_or_create(
        user=request.user,
        subscription=Subscription.objects.get(name="Atom"))

    expires = datetime.date.today()
    us.expires = expires.replace(year=expires.year + 100)
    us.active = True
    us.cancelled = False
    us.subscribe()  # Adds user to group
    us.save()

    return HttpResponseRedirect(us.subscription.get_absolute_url())


@login_required
@require_POST
def atom_deactivate(request):
    try:
        us = UserSubscription.objects.get(
            user=request.user,
            subscription=Subscription.objects.get(name="Atom"))
        us.active = False
        us.cancelled = True
        us.unsubscribe()
        us.save()
    except UserSubscription.DoesNotExist:
        return HttpResponseForbidden()

    return HttpResponseRedirect(us.subscription.get_absolute_url())
