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
def astrobin_user(context, user, layout="standard"):
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

    return {
        'request': request,
        'layout': layout,
        'view': request.GET.get('view', 'default'),

        'user': user,
        'request_user': request_user,

        'images': images,
        'followers': followers,
        'following': following,
    }


@register.inclusion_tag('astrobin_apps_users/inclusion_tags/user_list.html', takes_context = True)
def astrobin_apps_users_list(context, user_list, layout="standard"):
    request = context['request']

    request_user = None
    if request.user.is_authenticated():
        request_user = User.objects.get(pk = request.user.pk)


    return {
        'request': request,
        'request_user': request_user,
        'user_list': user_list,
        'layout': layout,
        'view': request.GET.get('view', 'default'),
        'STATIC_URL': settings.STATIC_URL,
    }

