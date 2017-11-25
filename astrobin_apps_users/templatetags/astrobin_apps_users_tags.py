# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.template import Library, Node
from django.utils.translation import ugettext_lazy as _

# AstroBin apps
from astrobin.models import Image
from astrobin_apps_premium.utils import premium_user_has_valid_subscription

# Third party apps
from toggleproperties.models import ToggleProperty


register = Library()


@register.inclusion_tag('astrobin_apps_users/inclusion_tags/astrobin_username.html')
def astrobin_username(user, **kwargs):
    if not hasattr(user, 'userprofile'):
        try:
            user = User.objects.get(username = user)
        except User.DoesNotExist:
            return {'user': None}

    display_name = user.userprofile.get_display_name()
    is_superuser = user.is_superuser
    is_image_moderator = user.userprofile.is_image_moderator()
    is_iotd_staff = user.userprofile.is_iotd_staff()
    is_iotd_submitter = user.userprofile.is_iotd_submitter()
    is_iotd_reviewer = user.userprofile.is_iotd_reviewer()
    is_iotd_judge = user.userprofile.is_iotd_judge()
    is_premium = premium_user_has_valid_subscription(user)

    classes = ['astrobin-username']
    titles = []

    if is_superuser:
        classes.append('astrobin-superuser')
        titles.append(_('Administrator'))

    if is_image_moderator:
        classes.append('astrobin-image-moderator')
        titles.append(_('Image moderator'))

    if is_iotd_staff:
        classes.append(' astrobin-iotd-staff')

    if is_iotd_submitter:
        classes.append(' astrobin-iotd-submitter')
        titles.append(_('IOTD Submitter'))

    if is_iotd_reviewer:
        classes.append(' astrobin-iotd-reviewer')
        titles.append(_('IOTD Reviewer'))

    if is_iotd_judge:
        classes.append(' astrobin-iotd-judge')
        titles.append(_('IOTD Judge'))

    if is_premium:
        classes.append(' astrobin-premium-member')
        titles.append(_('Premium member'))

    return {
        'user': user,
        'display_name': display_name,
        'is_superuser': is_superuser,
        'is_image_moderator': is_image_moderator,
        'is_iotd_staff': is_iotd_staff,
        'is_premium': is_premium,
        'classes': classes,
        'titles': titles,
        'link': kwargs.get('link', True),
    }


@register.inclusion_tag('astrobin_apps_users/inclusion_tags/astrobin_user.html', takes_context = True)
def astrobin_user(context, user, **kwargs):
    user_ct = ContentType.objects.get_for_model(User)
    images = Image.objects.filter(user = user).count()
    followers = ToggleProperty.objects.toggleproperties_for_object("follow", user).count()
    following = ToggleProperty.objects.filter(
        property_type = "follow",
        user = user,
        content_type = user_ct).count()

    request = context['request']
    request_user = None
    if request.user.is_authenticated():
        request_user = User.objects.get(pk = request.user.pk)

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
        'images': images,
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
        request_user = User.objects.get(pk = request.user.pk)

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
        'STATIC_URL': settings.STATIC_URL,
        'DONATIONS_ENABLED': context['DONATIONS_ENABLED'],
        'PREMIUM_ENABLED': context['PREMIUM_ENABLED'],
    }

