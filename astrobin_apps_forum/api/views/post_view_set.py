from collections import namedtuple

import simplejson
from annoying.functions import get_object_or_None
from django.db.models import QuerySet
from django.http import HttpResponse
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
from pybb.models import Post
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.permissions import CustomForumPermissions
from astrobin_apps_forum.api.filters.post_filter import PostFilter
from astrobin_apps_forum.api.serializers.post_serializer import PostSerializer
from common.permissions import ReadOnly


class PostViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    serializer_class = PostSerializer
    permission_classes = [ReadOnly]
    filter_class = PostFilter
    http_method_names = ['get', 'put', 'head']

    def get_queryset(self) -> QuerySet:
        queryset = Post.objects.filter(on_moderation=False)
        return CustomForumPermissions().filter_posts(self.request.user, queryset)

    @action(detail=True, methods=['put'], permission_classes=[AllowAny])
    def hit(self, request, pk):
        UpdateHitCountResponse = namedtuple('UpdateHitCountResponse', 'hit_counted hit_message')

        post: Post = get_object_or_None(self.get_queryset(), pk=pk)

        if post and request.user != post.user:
            try:
                hit_count: HitCount = HitCount.objects.get_for_object(post)
            except HitCount.MultipleObjectsReturned:
                hit_count = HitCount.objects.filter(object_pk=post.pk).first()
                HitCount.objects.filter(
                    content_type=hit_count.content_type,
                    object_pk=post.pk
                ).exclude(
                    pk=hit_count.pk
                ).delete()
            hit_count_response: UpdateHitCountResponse = HitCountMixin.hit_count(request, hit_count)
            return HttpResponse(simplejson.dumps(hit_count_response))

        return HttpResponse(
            simplejson.dumps(UpdateHitCountResponse(False, 'Hit from author or moderated or missing post ignored'))
        )

    @action(detail=True, methods=['get'], permission_classes=[AllowAny], url_path='hit-count')
    def hit_count(self, request, pk):
        post: Post = get_object_or_404(self.get_queryset(), pk=pk)
        count: HitCount = HitCount.objects.get_for_object(post)
        return HttpResponse(simplejson.dumps({'count': count.hits}))
