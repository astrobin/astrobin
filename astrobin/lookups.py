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

from django.db.models import Q 
from django.db import IntegrityError
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings

import simplejson
import urllib2
import string
import re


@login_required
@require_GET
def autocomplete(request, what):
    values = []
    q = request.GET['q']
    limit = 10
    regex = ".*"

    for c in re.sub(r'\s', '', q):
        regex += "%c.*" % re.escape(c)

    # Subjects have a special case because their name is in the mainId field.
    if what == 'subjects':
        # First search for the mainId
        values = Subject.objects.filter(Q(mainId__regex=r'%s'%regex))[:limit]
        if values:
            return HttpResponse(simplejson.dumps([{'id': str(v.id), 'name': v.mainId} for v in values]))
        # If not found, search for the alternative ids
        values = SubjectIdentifier.objects.filter(Q(identifier__regex=r'%s'%regex))[:limit]
        if values:
            return HttpResponse(simplejson.dumps(
                [{'id': str(v.subject.id), 'name': "%s (%s)" % (v.subject.mainId, v.identifier) } for v in values]))
        # If we're still not finding it, then query Simbad
        url = settings.SIMBAD_SEARCH_QUERY_URL + urllib2.quote(q)
        json_string = ""
        try:
            f = urllib2.urlopen(url, timeout=1)
            json_string = f.read()
        except:
            return HttpResponse(simplejson.dumps([{}]))
        try:
            # json will be a list of dictionaries with simbad objects.
            json = simplejson.loads(json_string)
        except simplejson.JSONDecodeError:
            # Malformatted query and Simbad didn't accept it. Let's
            # ignore it
            f.close()
            return HttpResponse(simplejson.dumps([{}]))

        # Reset values, which might be of QuerySet type.
        values = []
        for obj in json:
            found = False

            # We need to add it to our database first. We
            # are actally saving this early, because the user might
            # just disregard this result and select another, or
            # navigate away from the page. This might not be
            # optimal, but we need to have an object id in our
            # database if the user does decide to use this object.
            s = Subject()
            s.initFromJSON(obj)
            try:
                s.save()
            except IntegrityError:
                # Sometimes, for a racecondition somewhere, if the
                # user tries to lookups names really fast, a name that
                # is going to the database gets looked up again before
                # it really is there. So we try to save it again and
                # get the IntegrityError because of the duplicate key.
                s = Subject.objects.get(mainId=obj['mainId'])

            # We need to make sure that q is part of the mainId, or the
            # ui will be very confused. If that's not the case, then
            # we construct a string that has both the mainId and the id
            # that was found, just like above.
            if re.match(regex, obj['mainId'], flags=re.IGNORECASE):
                found = True
                values.append(
                    {'id': str(s.id),
                     'name': obj['mainId']})

            # The id that matched q is actually one of the
            # alternative ids. Let's find it.
            for id in obj['idlist']:
                # We've got to save also all the alternative ids
                # in our database if we want to stay true to our
                # caching philosophy.
                sid = SubjectIdentifier(identifier=id, subject=s)
                try:
                    sid.save()
                except IntegrityError:
                    # It looks like we picked this name on a previous
                    # pass. It's all right.
                    pass
                if not found and re.match(regex, id, flags=re.IGNORECASE):
                    values.append(
                        {'id': str(s.id),
                         'name': "%s (%s)" % (obj['mainId'], id)})

        f.close()
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

