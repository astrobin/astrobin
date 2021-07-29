from functools import reduce

import operator

from django.db.models import Q
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_read_only import IsEquipmentModeratorOrReadOnly


class EquipmentItemViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [IsEquipmentModeratorOrReadOnly]
    http_method_names = ['get', 'post', 'head', 'put', 'patch']

    def get_queryset(self):
        q = self.request.GET.get('q')
        manager = self.get_serializer().Meta.model.objects

        if q:
            words = q.split(' ')
            name_filters = reduce(operator.or_, [Q(**{'name__icontains': x}) for x in words])
            make_filters = reduce(operator.or_, [Q(**{'brand__name__icontains': x}) for x in words])
            return manager.filter(name_filters | make_filters)

        return manager.all()

    class Meta:
        abstract = True
