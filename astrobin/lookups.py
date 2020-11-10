import re

import simplejson
from avatar.utils import get_primary_avatar, get_default_avatar_url
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.utils.encoding import smart_str
from django.views.decorators.http import require_GET

from models import Accessory, Image
from models import Camera
from models import Filter
from models import FocalReducer
from models import Location
from models import Mount
from models import Software
from models import Telescope
from models import UserProfile


@require_GET
def autocomplete(request, what):
    values = []
    if 'q' not in request.GET:
        return HttpResponse(simplejson.dumps([{}]))

    q = smart_str(request.GET['q'])
    limit = 10

    regex = ".*%s.*" % re.escape(q)
    for k, v in {'locations': Location,
                 'telescopes': Telescope,
                 'imaging_telescopes': Telescope,
                 'guiding_telescopes': Telescope,
                 'mounts': Mount,
                 'cameras': Camera,
                 'imaging_cameras': Camera,
                 'guiding_cameras': Camera,
                 'focal_reducers': FocalReducer,
                 'software': Software,
                 'filters': Filter,
                 'accessories': Accessory}.iteritems():
        if what == k:
            values = v.objects.filter(Q(make__iregex=r'%s' % regex) | Q(name__iregex=r'%s' % regex))[:limit]
            if k == 'locations':
                return HttpResponse(simplejson.dumps([{'id': str(v.id), 'name': v.name} for v in values]))
            else:
                return HttpResponse(simplejson.dumps([{'id': str(v.id), 'name': unicode(v)} for v in values]))

    return HttpResponse(simplejson.dumps([{}]))


@login_required
@require_GET
def autocomplete_user(request, what):
    profile = request.user.userprofile
    values = ()
    for k, v in {'telescopes': profile.telescopes,
                 'imaging_telescopes': profile.telescopes,
                 'guiding_telescopes': profile.telescopes,
                 'mounts': profile.mounts,
                 'cameras': profile.cameras,
                 'imaging_cameras': profile.cameras,
                 'guiding_cameras': profile.cameras,
                 'focal_reducers': profile.focal_reducers,
                 'software': profile.software,
                 'filters': profile.filters,
                 'accessories': profile.accessories}.iteritems():
        if what == k:
            values = v.all().filter(Q(name__icontains=request.GET['q']))

    return HttpResponse(simplejson.dumps([{'id': str(v.id), 'name': v.name} for v in values]))


@login_required
@require_GET
def autocomplete_usernames(request):
    if 'q' not in request.GET:
        HttpResponse(simplejson.dumps([]))

    q = request.GET['q']

    users = UserProfile.objects.filter(
        Q(user__username__icontains=q) |
        Q(user__userprofile__real_name__icontains=q)
    ).distinct()[:10]

    results = []

    for user in users:
        avatar = get_primary_avatar(user, 40)
        if avatar is None:
            avatar_url = get_default_avatar_url()
        else:
            avatar_url = avatar.get_absolute_url()

        results.append({
            'id': str(user.id),
            'username': user.user.username,
            'realName': user.user.userprofile.real_name,
            'displayName': user.user.userprofile.real_name if user.user.userprofile.real_name else user.user.username,
            'avatar': avatar_url,
        })

    return HttpResponse(simplejson.dumps(results))


@login_required
@require_GET
def autocomplete_images(request):
    if 'q' not in request.GET:
        HttpResponse(simplejson.dumps([]))

    q = request.GET['q']

    images = Image.objects_including_wip.filter(user=request.user, title__icontains=q)[:10]

    results = []

    for image in images:
        results.append({
            'id': image.get_id(),
            'title': image.title,
            'thumbnail': image.thumbnail('gallery', {'sync': True}),
            'url': image.get_absolute_url(),
        })

    return HttpResponse(simplejson.dumps(results))
