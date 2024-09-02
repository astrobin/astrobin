# -*- coding: utf-8 -*-
from django.db.models import QuerySet
from rest_framework import viewsets

from astrobin.api2.serializers.collection_serializer import CollectionSerializer
from astrobin.models import Collection
from common.permissions import ReadOnly


class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer
    permission_classes = [ReadOnly]

    def get_queryset(self) -> QuerySet:
        if 'user' in self.request.GET:
            return Collection.objects.filter(user__pk=self.request.GET['user'])

        if 'ids' in self.request.GET:
            return Collection.objects.filter(pk__in=self.request.GET.get('ids', '').split(','))

        if not self.request.user.is_authenticated:
            return Collection.objects.none()

        return Collection.objects.filter(user=self.request.user)
