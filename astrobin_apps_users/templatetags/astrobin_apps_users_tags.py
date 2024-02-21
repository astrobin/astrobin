import logging

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.template import Library
from django.utils.translation import ugettext_lazy as _

from astrobin.models import UserProfile
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_users.services import UserService
from toggleproperties.models import ToggleProperty

log = logging.getLogger(__name__)

register = Library()


@register.inclusion_tag('astrobin_apps_users/inclusion_tags/astrobin_username.html', takes_context=True)
def astrobin_username(context, user, **kwargs):
    from common.services.caching_service import CachingService

    if not hasattr(user, 'userprofile'):
        try:
            user = UserProfile.objects.get(user__username=user).user
        except UserProfile.DoesNotExist:
            return {'user': None}

    classes = ['astrobin-username']
    titles = []
    link = kwargs.get('link', True)

    if link:
        cache_key = 'user_metadata_' + user.username
        user_metadata = CachingService().get(cache_key)
        if user_metadata is None:
            user_metadata = {
                'display_name': user.userprofile.get_display_name(),
                'is_superuser': user.is_superuser,
                'is_image_moderator': user.userprofile.is_image_moderator(),
                'is_iotd_staff': user.userprofile.is_iotd_staff(),
                'is_iotd_submitter': user.userprofile.is_iotd_submitter(),
                'is_iotd_reviewer': user.userprofile.is_iotd_reviewer(),
                'is_iotd_judge': user.userprofile.is_iotd_judge(),
                'is_premium': PremiumService(user).get_valid_usersubscription() is not None
            }

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

            CachingService.set(cache_key, user_metadata, 300)
    else:
        user_metadata = {
            'display_name': user.userprofile.get_display_name(),
        }

    return {
        **user_metadata,
        'request': context['request'],
        'user': user,
        'classes': classes,
        'titles': titles,
        'link': link,
    }


@register.inclusion_tag('astrobin_apps_users/inclusion_tags/astrobin_user.html', takes_context=True)
def astrobin_user(context, user, **kwargs):
    request = context['request']

    images = UserService(user).get_public_images()
    followers = user.userprofile.followers_count
    following = user.userprofile.following_count

    request_user = None
    if request.user.is_authenticated:
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


@register.inclusion_tag('astrobin_apps_users/inclusion_tags/user_list.html', takes_context=True)
def astrobin_apps_users_list(context, user_list, **kwargs):
    request = context['request']

    request_user = None
    if request.user.is_authenticated:
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


@register.filter
def is_mutual_follower(a, b):
    # type: (User, User) -> bool

    user_ct = ContentType.objects.get_for_model(User)
    a_b = ToggleProperty.objects.filter(property_type='follow', object_id=b.id, content_type=user_ct, user=a).exists()
    b_a = ToggleProperty.objects.filter(property_type='follow', object_id=a.id, content_type=user_ct, user=b).exists()

    return a_b and b_a


@register.filter
def contribution_index(user):
    if hasattr(user, 'userprofile'):
        if user.userprofile.contribution_index is not None:
            return user.userprofile.contribution_index

    return 0
