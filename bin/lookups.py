from models import Telescope
from django.db.models import Q 
from django.http import HttpResponse
import simplejson

def autocomplete(request, what):
    values = ()
    if what == 'telescopes':
        values = Telescope.objects.filter(Q(name__istartswith=request.GET['q']))

    return HttpResponse(simplejson.dumps([{'value_unused': str(v.id), 'name': v.name} for v in values]))

