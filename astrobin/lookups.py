from models import Telescope
from models import Mount
from models import Camera
from models import FocalReducer
from models import Software
from models import Filter
from models import Subject
from models import UserProfile

from django.db.models import Q 
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required

import simplejson

@login_required
@require_GET
def autocomplete(request, what):
    values = ()
    for k, v in {'telescopes':Telescope,
                 'mounts':Mount,
                 'cameras':Camera,
                 'focal_reducers':FocalReducer,
                 'software':Software,
                 'subjects':Subject,
                 'filters':Filter}.iteritems():
        if what == k:
            values = v.objects.filter(Q(name__icontains=request.GET['q']))

    return HttpResponse(simplejson.dumps([{'value_unused': str(v.id), 'name': v.name} for v in values]))


@login_required
@require_GET
def autocomplete_user(request, what):
    profile = UserProfile.objects.get(user=request.user)
    values = ()
    for k, v in {'telescopes':profile.telescopes,
                 'mounts':profile.mounts,
                 'cameras':profile.cameras,
                 'focal_reducers':profile.focal_reducers,
                 'software':profile.software,
                 'filters':profile.filters}.iteritems():
        if what == k:
            values = v.all().filter(Q(name__icontains=request.GET['q']))

    return HttpResponse(simplejson.dumps([{'value_unused': str(v.id), 'name': v.name} for v in values]))

