import logging
from collections import namedtuple

import simplejson
from braces.views import JSONResponseMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.views.generic.base import View
from hitcount.models import HitCount
from hitcount.views import HitCountMixin

log = logging.getLogger(__name__)


class RecordHit(JSONResponseMixin, View):
    def post(self, request, *args, **kwargs):
        data = simplejson.loads(request.body.decode('utf-8'))

        object_id = data.get('object_id')
        content_type_id = data.get('content_type_id')

        obj = ContentType.objects.get_for_id(content_type_id).get_object_for_this_type(pk=object_id)

        UpdateHitCountResponse = namedtuple('UpdateHitCountResponse', 'hit_counted hit_message')
        hit_count: HitCount = HitCount.objects.get_for_object(obj)
        hit_count_response: UpdateHitCountResponse = HitCountMixin.hit_count(request, hit_count)

        return HttpResponse(simplejson.dumps(hit_count_response))
