from models import Telescope
from django.db.models import Q 

class TelescopeLookup(object):
    def get_query(self,q,request):
        return Telescope.objects.filter(Q(name__istartswith=q))

    def format_item(self,telescope):
        return unicode(telescope)

    def format_result(self,telescope):
        return "%s<br/>" % unicode(telescope)

    def get_objects(self,ids):
        return Telescope.objects.filter(pk__in=ids).order_by('name')

