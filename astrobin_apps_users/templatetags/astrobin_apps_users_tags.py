# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.template import Library, Node

# AstroBin apps
from astrobin.models import Image

# Third party apps
from toggleproperties.models import ToggleProperty


register = Library()

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

