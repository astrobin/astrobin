import operator
from functools import reduce

from django.contrib.postgres.search import TrigramDistance
from django.db.models import Q
from django.utils import timezone
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

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
            brand_filters = reduce(operator.or_, [Q(**{'brand__name__icontains': x}) for x in words])
            return manager.filter(name_filters | brand_filters)[:10]

        return manager.all()

    @action(
        detail=False,
        methods=['GET'],
        url_path='find-similar-in-brand',
    )
    def find_similar_in_brand(self, request):
        brand = request.GET.get('brand')
        q = request.GET.get('q')

        manager = self.get_serializer().Meta.model.objects
        objects = manager.none()

        if brand and q:
            objects = manager \
                .annotate(distance=TrigramDistance('name', q)) \
                .filter(Q(brand=int(brand)) & Q(Q(distance__lte=.7) | Q(name__icontains=q))) \
                .order_by('distance')[:10]

        serializer = self.serializer_class(objects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['PUT'])
    def approve(self, request, pk):
        item = get_object_or_404(self.get_serializer().Meta.model.objects, pk=pk)

        if item.reviewed_by is not None:
            return Response("This item was already reviewed", HTTP_400_BAD_REQUEST)

        item.reviewed_by = request.user
        item.reviewed_timestamp = timezone.now()
        item.reviewer_decision = 'APPROVED'
        item.reviewer_comment = request.data.get('comment')

        item.save()

        serializer = self.serializer_class(item)
        return Response(serializer.data)

    @action(detail=True, methods=['PUT'])
    def reject(self, request, pk):
        item = get_object_or_404(self.get_serializer().Meta.model.objects, pk=pk)

        if item.reviewed_by is not None:
            return Response("This item was already reviewed", HTTP_400_BAD_REQUEST)

        item.reviewed_by = request.user
        item.reviewed_timestamp = timezone.now()
        item.reviewer_decision = 'REJECTED'
        item.reviewer_comment = request.data.get('comment')

        item.save()

        serializer = self.serializer_class(item)
        return Response(serializer.data)

    def image_upload(self, request, pk):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, HTTP_400_BAD_REQUEST)

    class Meta:
        abstract = True
