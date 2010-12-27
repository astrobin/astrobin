from models import Telescope
from models import Mount
from models import Camera
from models import FocalReducer
from models import Software
from models import Filter
from models import Subject

from django.db.models import Q 
from django.http import HttpResponse
import simplejson

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
            values = v.objects.filter(Q(name__istartswith=request.GET['q']))

    return HttpResponse(simplejson.dumps([{'value_unused': str(v.id), 'name': v.name} for v in values]))

