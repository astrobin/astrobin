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
from django.utils.encoding import smart_str

from haystack.query import SearchQuerySet

import simplejson
import string
import re

INTERESTING_CATALOGS = (
    'NAME',
    'M',
    'NGC',
    'IC',
    'VDB',
    'SH',
)

@login_required
@require_GET
def autocomplete(request, what):
    values = []
    q = smart_str(request.GET['q'])
    limit = 10

    # Subjects have a special case because their name is in the mainId field.
    if what == 'subjects':
        db_values = SearchQuerySet().autocomplete(text = q).models(SubjectIdentifier)[:10]
        for v in db_values:
            if v.object.catalog in INTERESTING_CATALOGS:
                id = str(v.object.subject.id)
                name = v.object.identifier
                if v.object.catalog == 'NAME':
                    name = name[4:]

                item = {'id': id, 'name': name}
                if item not in values:
                    values.append(item)

        # Not enough? Search Subjects.
        if len(values) < 10:
            db_values = SearchQuerySet().autocomplete(text = q).models(Subject)[:10]
            for v in db_values:
                if (v.object.catalog and v.object.catalog in INTERESTING_CATALOGS) or not v.object.catalog:
                    id = str(v.object.id)
                    name = v.object.mainId
                    if v.object.catalog == 'NAME':
                        name = name[4:]

                    item = {'id': id, 'name': name}
                    if item not in values:
                        values.append(item)

        # If still not enough, query Simbad.
        if len(values) < 10:
            limit = 10 - len(values)
            subjects = simbad.find_subjects(q)[:limit]
            if subjects:
                for s in subjects:
                    name = s.mainId
                    if q.lower() not in name.lower():
                        sids = SubjectIdentifier.objects.filter(subject = s)
                        for sid in sids:
                            if q.lower() in sid.identifier.lower():
                                name = sid.identifier
                    split = name.split(' ')
                    if len(split) > 1:
                        catalog = split[0]
                        if catalog in INTERESTING_CATALOGS:
                            if catalog == 'NAME':
                                name = name[4:]
                            item = {'id': str(s.id), 'name': name}
                            if item not in values:
                                values.append(item)

        return HttpResponse(simplejson.dumps(values))

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
            values = v.objects.filter(Q(name__iregex=r'%s'%regex))[:limit]
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

