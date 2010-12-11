from models import Telescope
from django.db.models import Q 
from django.http import HttpResponse
import simplejson

def autocomplete(request, what):
    values = ()
    if what == 'telescopes':
        values = Telescope.objects.filter(Q(name__istartswith=request.GET['tag']))

    return HttpResponse(simplejson.dumps([{'key': v.name, 'value': v.id} for v in values]))

