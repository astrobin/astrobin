from models import Telescope
from models import Mount
from models import Camera
from models import FocalReducer
from models import Software
from models import Filter
from models import Accessory
from models import Subject, SubjectIdentifier
from models import Location
from models import UserProfile

import simbad

from django.db.models import Q 
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext as _

import simplejson
import string


@login_required
@require_GET
def autocomplete(request, what):
    values = []
    q = request.GET['q']
    limit = 10

    # Subjects have a special case because their name is in the mainId field.
    if what == 'subjects':
        subjects = simbad.find_subjects(q)
        if subjects:
            for s in subjects:
                id = s.mainId
                if q.lower() not in id.lower():
                    sids = SubjectIdentifier.objects.filter(subject = s)
                    for sid in sids:
                        if q.lower() in sid.identifier.lower():
                            id = sid.identifier
                values.append({'id': str(s.id), 'name': id})
            return HttpResponse(simplejson.dumps(values))

    for k, v in {'locations': Location,
                 'telescopes':Telescope,
                 'mounts':Mount,
                 'cameras':Camera,
                 'focal_reducers':FocalReducer,
                 'software':Software,
                 'filters':Filter,
                 'accessories':Accessory}.iteritems():
        if what == k:
            values = v.objects.filter(Q(name__regex=r'%s'%regex))[:limit]
            return HttpResponse(simplejson.dumps([{'id': str(v.id), 'name': v.name} for v in values]))

    return HttpResponse(simplejson.dumps([{}]))


@login_required
@require_GET
def autocomplete_user(request, what):
    profile = UserProfile.objects.get(user=request.user)
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
    values = User.objects.filter(Q(username__icontains=request.GET['q']))
    return HttpResponse(simplejson.dumps([{'id': str(v.id), 'name': v.username} for v in values]))

