from django.conf import settings
from django.db.models import Q
from notification import models as notifications

from astrobin.models import Request
from astrobin.models import UserProfile
from astrobin.models import Gear


def privatebeta_enabled(request):
    return {'privatebeta_enabled': settings.PRIVATEBETA_ENABLE_BETA}


def notices_count(request):
    response = {}
    if request.user.is_authenticated():
        response['notifications_count'] = notifications.Notice.objects.filter(Q(user = request.user) & Q(unseen = True)).count()
        response['requests_count'] = Request.objects.filter(Q(to_user = request.user) & Q(fulfilled = False)).count()

    return response


def user_language(request):
    d = {
        'user_language': request.LANGUAGE_CODE,
    }
    if request.user.is_authenticated():
        profile = UserProfile.objects.get(user = request.user)
        d['user_language'] = profile.language

    return d


def common_variables(request):
    d = {
        'random_gear_item': Gear.objects.filter(moderator_fixed = None).order_by('?')[:1].get(),
        'is_producer': request.user.groups.filter(name='Producers'),
        'is_retailer': request.user.groups.filter(name='Retailers'),
        'IMAGES_URL' : settings.IMAGES_URL,
    }

    return d

