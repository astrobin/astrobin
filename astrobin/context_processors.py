from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.utils.translation import ugettext as _

from notification import models as notifications

from astrobin.models import Request
from astrobin.models import Gear
from astrobin.models import Image
from astrobin.search_indexes import _prepare_rating
from astrobin.votes import index

from nested_comments.models import NestedComment


def privatebeta_enabled(request):
    return {'privatebeta_enabled': settings.PRIVATEBETA_ENABLE_BETA}


def notices_count(request):
    response = {}
    if request.user.is_authenticated():
        response['notifications_count'] = notifications.Notice.objects.filter(Q(recipient = request.user) & Q(unseen = True)).count()

    return response


def user_language(request):
    d = {
        'user_language': request.LANGUAGE_CODE,
    }
    if request.user.is_authenticated():
        profile = request.user.userprofile
        d['user_language'] = profile.language

    return d


def user_profile(request):
    d = {
        'userprofile': None,
    }

    if request.user.is_authenticated():
        profile = request.user.userprofile
        d['userprofile'] = profile

    return d


def user_scores(request):
    d = {
        'user_scores_index': 0,
        'user_scores_images': 0,
        'user_scores_comments': 0,
        'user_scores_followers': 0,
    }

    if request.user.is_authenticated():
        profile = request.user.userprofile
        all_images = Image.objects.filter(user = request.user, is_wip = False)
        followers = profile.followers.all().count()

        cache_key = "astrobin_user_score_%s" % request.user
        user_index = cache.get(cache_key)
        if user_index is None:

            if profile.optout_rating:
                d['user_scores_index'] = 0
            else:
                voted_images = Image.objects.filter(user = request.user, is_wip = False, allow_rating = True)
                l = []

                for i in voted_images:
                    l.append(_prepare_rating(i))
                if len(l) > 0:
                    user_index = index(l)
                    cache.set(cache_key, user_index, 3600)


        d['user_scores_index'] = user_index
        d['user_scores_images'] = all_images.count()
        d['user_scores_comments'] =  NestedComment.objects.filter(author = request.user, deleted = False).count()
        d['user_scores_followers'] = followers

    return d


def common_variables(request):
    from rawdata.utils import user_has_subscription

    d = {
        #'random_gear_item': Gear.objects.filter(moderator_fixed = None).order_by('?')[:1].get(),
        'is_producer': request.user.groups.filter(name='Producers'),
        'is_retailer': request.user.groups.filter(name='Retailers'),
        'has_rawdata_subscription': user_has_subscription(request.user),
        'IMAGES_URL' : settings.IMAGES_URL,
        'CDN_URL' : settings.CDN_URL,
    }

    return d

