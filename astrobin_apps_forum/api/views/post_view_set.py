from collections import namedtuple

import simplejson
from annoying.functions import get_object_or_None
from django.http import HttpResponse
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
from pybb.models import Post
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_forum.api.filters.post_filter import PostFilter
from astrobin_apps_forum.api.permissions.is_post_author_or_readonly import IsPostAuthorOrReadonly
from astrobin_apps_forum.api.serializers.post_serializer import PostSerializer


class PostViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    serializer_class = PostSerializer
    permission_classes = [IsPostAuthorOrReadonly]
    filter_class = PostFilter
    http_method_names = ['get', 'post', 'put', 'head']
    queryset = Post.objects.filter(on_moderation=False)

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            user_ip=self.request.META.get('REMOTE_ADDR'),
        )

    @action(detail=True, methods=['put'])
    def hit(self, request, pk):
        UpdateHitCountResponse = namedtuple('UpdateHitCountResponse', 'hit_counted hit_message')

        post: Post = get_object_or_None(self.queryset, pk=pk)

        if post and request.user != post.user:
            hit_count: HitCount = HitCount.objects.get_for_object(post)
            hit_count_response: UpdateHitCountResponse = HitCountMixin.hit_count(request, hit_count)
            return HttpResponse(simplejson.dumps(hit_count_response))

        return HttpResponse(
            simplejson.dumps(UpdateHitCountResponse(False, 'Hit from author or moderated or missing post ignored'))
        )
