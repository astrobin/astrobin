from models import Telescope
from models import Mount
from models import Camera
from models import FocalReducer
from models import Software
from models import Filter
from models import Accessory
from models import Location
from models import UserProfile

from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_str

import simplejson
import string
import re

@require_GET
def autocomplete(request, what):
    values = []
    if 'q' not in request.GET:
        return HttpResponse(simplejson.dumps([{}]))

    q = smart_str(request.GET['q'])
    limit = 10

    regex = ".*%s.*" % re.escape(q)
    for k, v in {'locations': Location,
                 'telescopes':Telescope,
                 'imaging_telescopes':Telescope,
                 'guiding_telescopes':Telescope,
                 'mounts':Mount,
                 'cameras':Camera,
                 'imaging_cameras':Camera,
                 'guiding_cameras':Camera,
                 'focal_reducers':FocalReducer,
                 'software':Software,
                 'filters':Filter,
                 'accessories':Accessory}.iteritems():
        if what == k:
            values = v.objects.filter(Q(make__iregex=r'%s'%regex) | Q(name__iregex=r'%s'%regex))[:limit]
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
    for k, v in {'telescopes':profile.telescopes,
                 'imaging_telescopes':profile.telescopes,
                 'guiding_telescopes':profile.telescopes,
                 'mounts':profile.mounts,
                 'cameras':profile.cameras,
                 'imaging_cameras':profile.cameras,
                 'guiding_cameras':profile.cameras,
                 'focal_reducers':profile.focal_reducers,
                 'software':profile.software,
                 'filters':profile.filters,
                 'accessories':profile.accessories}.iteritems():
        if what == k:
            values = v.all().filter(Q(name__icontains=request.GET['q']))

    return HttpResponse(simplejson.dumps([{'id': str(v.id), 'name': v.name} for v in values]))


@login_required
@require_GET
def autocomplete_usernames(request):
    values = UserProfile.objects.filter(Q(user__username__icontains=request.GET['q']))[:10]
    return HttpResponse(simplejson.dumps([{'id': str(v.id), 'name': v.user.username} for v in values]))

