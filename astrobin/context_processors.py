from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.translation import ugettext as _

from toggleproperties.models import ToggleProperty
from persistent_messages.models import Message

from astrobin.models import Request
from astrobin.models import Gear
from astrobin.models import Image

from nested_comments.models import NestedComment
from astrobin_apps_notifications.utils import get_unseen_notifications


def notices_count(request):
    response = {}
    if request.user.is_authenticated():
        count = get_unseen_notifications(request.user, -1).count()
        response['notifications_count'] = count

    return response


def user_language(request):
    d = {
        'user_language': getattr(request, "LANGUAGE_CODE", "en"),
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
    scores = {
        'user_scores_index': 0,
        'user_scores_followers': 0,
    }

    if request.user.is_authenticated():
        scores = request.user.userprofile.get_scores()

    return scores


def common_variables(request):
    from rawdata.utils import rawdata_user_has_valid_subscription
    from django_user_agents.utils import get_and_set_user_agent
    from django_bouncy.models import Bounce

    get_and_set_user_agent(request)

    bounced = False
    if request.user.is_authenticated():
        bounced = Bounce.objects.filter(
            address = request.user.email, bounce_type="Permanent").exists()

    d = {
        'True': True,
        'False': False,

        'LANGUAGE_CODE': request.LANGUAGE_CODE if 'LANGUAGE_CODE' in request else 'en',

        #'random_gear_item': Gear.objects.filter(moderator_fixed = None).order_by('?')[:1].get(),
        'is_producer': request.user.groups.filter(name='Producers'),
        'is_retailer': request.user.groups.filter(name='Retailers'),
        'rawdata_has_subscription': rawdata_user_has_valid_subscription(request.user),
        'IMAGES_URL' : settings.IMAGES_URL,
        'MEDIA_URL' : settings.MEDIA_URL,
        'ADS_ENABLED': settings.ADS_ENABLED,
        'DONATIONS_ENABLED': settings.DONATIONS_ENABLED,
        'PREMIUM_ENABLED': settings.PREMIUM_ENABLED,
        'PREMIUM_MAX_IMAGES_FREE': settings.PREMIUM_MAX_IMAGES_FREE,
        'PREMIUM_MAX_IMAGES_LITE': settings.PREMIUM_MAX_IMAGES_LITE,
        'PAYPAL_TEST': settings.PAYPAL_TEST,
        'IOTD_SHOW_CHOOSING_JUDGE': settings.IOTD_SHOW_CHOOSING_JUDGE,
        'SOLVING_ENABLED': settings.ENABLE_SOLVING,
        'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID,
        'READONLY_MODE': settings.READONLY_MODE,
        'HAS_BOUNCED_EMAILS': bounced
    }

    if request.user.is_authenticated() and request.user.userprofile.is_image_moderator():
        d['images_pending_moderation_no'] = Image.objects_including_wip.filter(moderator_decision = 0).count()

    return d
