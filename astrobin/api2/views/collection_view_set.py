# -*- coding: utf-8 -*-
from datetime import datetime

from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.api2.serializers.collection_add_remove_images_serializer import CollectionAddRemoveImagesSerializer
from astrobin.api2.serializers.collection_serializer import CollectionSerializer
from astrobin.models import Collection, Image
from common.permissions import IsObjectUserOrReadOnly


class CollectionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsObjectUserOrReadOnly]
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]

    def get_serializer_class(self):
        if self.request.query_params.get('action') == 'add-remove-images':
            return CollectionAddRemoveImagesSerializer

        return CollectionSerializer

    def get_queryset(self) -> QuerySet:
        queryset: QuerySet = Collection.objects.all()

        if 'user' in self.request.GET:
            queryset = queryset.filter(user__pk=self.request.GET.get('user'))

        if 'ids' in self.request.GET:
            queryset = queryset.filter(pk__in=self.request.GET.get('ids', '').split(','))

        if 'parent' in self.request.GET:
            parent = self.request.GET.get('parent')
            if parent == 'null':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent__pk=parent)
        else:
            # When no parent filter is applied, order by parent__isnull=True first
            queryset = queryset.order_by('-parent__isnull', 'id')

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

    @action(detail=True, methods=['post'], url_path='add-image')
    def add_image(self, request, pk=None):
        collection = self.get_object()

        if 'image' not in request.data:
            return Response({'detail': 'You must provide an image parameter.'}, status=400)

        try:
            image = Image.objects_including_wip_plain.get(pk=request.data['image'])
        except Image.DoesNotExist:
            return Response({'detail': 'Image does not exist.'}, status=400)

        if collection.user != request.user:
            return Response({'detail': 'You can only add images to your own collection.'}, status=400)

        if image.user != request.user and request.user not in image.collaborators.all():
            return Response({'detail': 'You can only add your own images to a collection.'}, status=400)

        if Image.objects_including_wip_plain.filter(pk=image.pk, collections=collection).exists():
            return Response({'detail': 'Image is already in collection.'}, status=400)

        image.collections.add(collection)
        collection.update_counts(save=False)
        collection.update_cover()
        Image.objects_including_wip_plain.filter(pk=image.pk).update(updated=datetime.now())

        return Response({'detail': 'Image added to collection.'})

    @action(detail=True, methods=['post'], url_path='remove-image')
    def remove_image(self, request, pk=None):
        collection = self.get_object()

        if 'image' not in request.data:
            return Response({'detail': 'You must provide an image parameter.'}, status=400)

        try:
            image = Image.objects_including_wip_plain.get(pk=request.data['image'])
        except Image.DoesNotExist:
            return Response({'detail': 'Image does not exist.'}, status=400)

        if collection.user != request.user:
            return Response({'detail': 'You can only remove images from your own collection.'}, status=400)

        if image.user != request.user and request.user not in image.collaborators.all():
            return Response({'detail': 'You can only remove your own images from a collection.'}, status=400)

        if not Image.objects_including_wip_plain.filter(pk=image.pk, collections=collection).exists():
            return Response({'detail': 'Image is not in collection.'}, status=400)

        image.collections.remove(collection)
        image.collections.filter(cover=image).update(cover=None)
        collection.update_counts(save=False)
        collection.update_cover()
        Image.objects_including_wip_plain.filter(pk=image.pk).update(updated=datetime.now())

        return Response({'detail': 'Image removed from collection.'})

    @action(detail=True, methods=['post'], url_path='set-cover-image')
    def set_cover_image(self, request, pk=None):
        collection: Collection = self.get_object()

        if 'image' not in request.data:
            return Response({'detail': 'You must provide an image parameter.'}, status=400)

        try:
            image = Image.objects_including_wip_plain.get(pk=request.data['image'])
        except Image.DoesNotExist:
            return Response({'detail': 'Image does not exist.'}, status=400)

        if collection.user != request.user:
            return Response({'detail': 'You can only set the cover image of your own collection.'}, status=400)

        if image.user != request.user:
            return Response(
                {'detail': 'You can only set your own images as the cover image of a collection.'}, status=400
            )

        if not Image.objects_including_wip_plain.filter(pk=image.pk, collections=collection).exists():
            return Response({'detail': 'Image is not in collection.'}, status=400)

        collection.cover = image
        collection.update_cover()

        serializer = self.get_serializer(collection)
        return Response(serializer.data)
