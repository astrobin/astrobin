# -*- coding: utf-8 -*-
from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.response import Response

from astrobin.api2.serializers.collection_serializer import CollectionSerializer
from astrobin.models import Collection
from common.permissions import ReadOnly


class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer
    permission_classes = [ReadOnly]

    def get_queryset(self) -> QuerySet:
        queryset: QuerySet = Collection.objects.all()

        if 'user' in self.request.GET:
            queryset = queryset.filter(user__pk=self.request.GET.get('user'))
        else:
            queryset = queryset.filter(user=self.request.user)

        if 'ids' in self.request.GET:
            queryset = queryset.filter(pk__in=self.request.GET.get('ids', '').split(','))

        if 'parent' in self.request.GET:
            parent = self.request.GET.get('parent')
            if parent == 'null':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent__pk=self.request.GET.get('parent'))

        return queryset

    def list(self, request, *args, **kwargs):
        if 'user' not in request.GET and 'ids' not in request.GET and 'parent' not in request.GET:
            return Response({'detail': 'You must provide a user, ids or parent parameter.'}, status=400)

        if 'ids' in request.GET:
            ids = request.GET.get('ids')
            if not ids:
                return Response({'detail': 'ids parameter cannot be empty.'}, status=400)

            ids = ids.split(',')
            if len(ids) > 100:
                return Response({'detail': 'You cannot request more than 100 collections at once.'}, status=400)

        return super().list(request, *args, **kwargs)
