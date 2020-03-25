# Django
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.template import Library, Node
from django.utils.translation import ugettext_lazy as _

# AstroBin apps
from astrobin.models import Image, UserProfile
from astrobin_apps_premium.utils import premium_user_has_valid_subscription

# Third party apps
from astrobin_apps_users.services import UserService
from toggleproperties.models import ToggleProperty


register = Library()


@register.inclusion_tag('astrobin_apps_users/inclusion_tags/astrobin_username.html', takes_context=True)
def astrobin_username(context, user, **kwargs):
    if not hasattr(user, 'userprofile'):
        try:
            user = UserProfile.objects.get(user__username = user).user
        except UserProfile.DoesNotExist:
            return {'user': None}

    cache_key = 'user_metadata_' + user.username
    user_metadata = cache.get(cache_key)
    if user_metadata is None:
        user_metadata = {}
        user_metadata['display_name'] = user.userprofile.get_display_name()
        user_metadata['is_superuser'] = user.is_superuser
        user_metadata['is_image_moderator'] = user.userprofile.is_image_moderator()
        user_metadata['is_iotd_staff'] = user.userprofile.is_iotd_staff()
        user_metadata['is_iotd_submitter'] = user.userprofile.is_iotd_submitter()
        user_metadata['is_iotd_reviewer'] = user.userprofile.is_iotd_reviewer()
        user_metadata['is_iotd_judge'] = user.userprofile.is_iotd_judge()
        user_metadata['is_premium'] = premium_user_has_valid_subscription(user)
        cache.set(cache_key, user_metadata, 600)
    else:
        display_name = user_metadata['display_name']
        is_superuser = user_metadata['is_superuser']
        is_image_moderator = user_metadata['is_image_moderator']
        is_iotd_staff = user_metadata['is_iotd_staff']
        is_iotd_submitter = user_metadata['is_iotd_submitter']
        is_iotd_reviewer = user_metadata['is_iotd_reviewer']
        is_iotd_judge = user_metadata['is_iotd_judge']
        is_premium = user_metadata['is_premium']

    classes = ['astrobin-username']
    titles = []

    if user_metadata['is_superuser']:
        classes.append('astrobin-superuser')
        titles.append(_('Administrator'))

    if user_metadata['is_image_moderator']:
        classes.append('astrobin-image-moderator')
        titles.append(_('Image moderator'))

    if user_metadata['is_iotd_staff']:
        classes.append(' astrobin-iotd-staff')

    if user_metadata['is_iotd_submitter']:
        classes.append(' astrobin-iotd-submitter')
        titles.append(_('IOTD Submitter'))

    if user_metadata['is_iotd_reviewer']:
        classes.append(' astrobin-iotd-reviewer')
        titles.append(_('IOTD Reviewer'))

    if user_metadata['is_iotd_judge']:
        classes.append(' astrobin-iotd-judge')
        titles.append(_('IOTD Judge'))

    if user_metadata['is_premium']:
        classes.append(' astrobin-premium-member')
        titles.append(_('Premium member'))

    response = user_metadata
    response.update({
        'request': context['request'],
        'user': user,
        'classes': classes,
        'titles': titles,
        'link': kwargs.get('link', True),
    })

    return response


@register.inclusion_tag('astrobin_apps_users/inclusion_tags/astrobin_user.html', takes_context = True)
def astrobin_user(context, user, **kwargs):
    request = context['request']

    user_ct = ContentType.objects.get_for_model(User)
    images = Image.objects.filter(user = user)
    if request.user != user:
        images = images.exclude(UserService.corrupted_query())

    followers = ToggleProperty.objects.toggleproperties_for_object("follow", user).count()
    following = ToggleProperty.objects.filter(
        property_type = "follow",
        user = user,
        content_type = user_ct).count()

    request_user = None
    if request.user.is_authenticated():
        request_user = UserProfile.objects.get(user=request.user).user

    view = kwargs.get('view')
    if view is None and 'view' in context:
        view = context['view']
    if view is None:
        view = request.GET.get('view', 'default'),

    layout = kwargs.get('layout')
    if layout is None and 'layout' in context:
        layout = context['layout']
    if layout is None:
        layout = request.GET.get('layout', 'default')

    return {
        'request': request,
        'user': user,
        'request_user': request_user,
        'view': view,
        'layout': layout,
        'user_is_owner': request.user == user,
        'images': images.count(),
        'followers': followers,
        'following': following,

        'DONATIONS_ENABLED': context['DONATIONS_ENABLED'],
        'PREMIUM_ENABLED': context['PREMIUM_ENABLED'],
    }


@register.inclusion_tag('astrobin_apps_users/inclusion_tags/user_list.html', takes_context = True)
def astrobin_apps_users_list(context, user_list, **kwargs):
    request = context['request']

    request_user = None
    if request.user.is_authenticated():
        request_user = UserProfile.objects.get(user=request.user).user

    view = kwargs.get('view')
    if view is None and 'view' in context:
        view = context['view']
    if view is None:
        view = request.GET.get('view', 'default'),

    layout = kwargs.get('layout')
    if layout is None and 'layout' in context:
        layout = context['layout']
    if layout is None:
        layout = request.GET.get('layout', 'default')

    return {
        'request': request,
        'request_user': request_user,
        'user_list': user_list,
        'view': view,
        'layout': layout,
        'DONATIONS_ENABLED': context['DONATIONS_ENABLED'],
        'PREMIUM_ENABLED': context['PREMIUM_ENABLED'],
    }

