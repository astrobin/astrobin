import simplejson
from avatar.utils import get_primary_avatar, get_default_avatar_url
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import TrigramDistance
from django.db.models import Q, Value
from django.db.models.functions import Concat, Lower
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from rest_framework.authtoken.models import Token

from astrobin.models import Image
from astrobin.models import UserProfile


@login_required
@require_GET
def autocomplete_private_message_recipients(request):
    if 'q' not in request.GET:
        return HttpResponse(simplejson.dumps([]))

    q = str(request.GET['q']).replace(chr(160), ' ')
    limit = 10
    results = []

    users = list(UserProfile.objects.filter(
        Q(user__username__icontains=q) | Q(real_name__icontains=q)
    ).distinct()[:limit])

    for user in users:
        results.append({
            'id': user.user.username,
            'realName': user.user.userprofile.real_name,
            'displayName': user.user.userprofile.real_name if user.user.userprofile.real_name else user.user.username,
        })

    return HttpResponse(simplejson.dumps(results))

@require_GET
def autocomplete_usernames(request):
    if 'q' not in request.GET:
        return HttpResponse(simplejson.dumps([]))

    if request.user.is_anonymous:
        if 'token' not in request.GET:
            return HttpResponse(simplejson.dumps([]))

        try:
            Token.objects.get(key=request.GET.get('token'))
        except Token.DoesNotExist:
            return HttpResponse(simplejson.dumps([]))

    q = request.GET['q']
    limit = 10
    results = []

    # Replace non-breaking space with regular space
    q = q.replace(chr(160), ' ')

    if 'postgresql' in settings.DATABASES['default']['ENGINE']:
        users = UserProfile.objects.annotate(
            name=Lower(Concat('real_name', Value(' '), 'user__username'))
        ).annotate(
            distance=TrigramDistance('name', q.lower())
        ).filter(
            Q(distance__lte=0.7) | Q(user__username__icontains=q) | Q(real_name__icontains=q)
        ).order_by('distance')
    else:
        users = UserProfile.objects.annotate(
            name=Lower(Concat('real_name', Value(' '), 'user__username'))
        ).filter(
            name__icontains=q
        )

    users = users.values_list('user__id', 'user__username', 'real_name')[:limit]

    for user in users.iterator():
        avatar = get_primary_avatar(user, 40)
        if avatar is None:
            avatar_url = get_default_avatar_url()
        else:
            avatar_url = avatar.get_absolute_url()

        results.append({
            'id': str(user[0]),
            'username': user[1],
            'realName': user[2],
            'displayName': user[2] if user[2] else user[1],
            'avatar': avatar_url,
        })

    return HttpResponse(simplejson.dumps(results))


@require_GET
def autocomplete_images(request):
    if 'q' not in request.GET:
        HttpResponse(simplejson.dumps([]))

    if request.user.is_anonymous:
        if 'token' not in request.GET:
            return HttpResponse(simplejson.dumps([]))

        try:
            token = Token.objects.get(key=request.GET.get('token'))
            user = token.user
        except Token.DoesNotExist:
            return HttpResponse(simplejson.dumps([]))
    else:
        user = request.user

    q = request.GET['q']

    # Replace non-breaking space with regular space
    q = q.replace(chr(160), ' ')

    images = Image.objects_including_wip.filter(user=user, title__icontains=q)[:10]

    results = []

    for image in images:
        results.append({
            'id': image.get_id(),
            'title': image.title,
            'thumbnail': image.thumbnail('gallery', None, sync=True),
            'url': image.get_absolute_url(),
        })

    return HttpResponse(simplejson.dumps(results))
